# FastAPI приложение gns3-service.

import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.config import settings
from src.observability.logging import configure_logging
from src.observability.sentry import configure_sentry

configure_logging("gns3-service", level=getattr(getattr(settings, "service", None), "log_level", "INFO"))
configure_sentry("gns3-service", environment=os.getenv("ENVIRONMENT", "dev"))

from src.clients.admin import GNS3AdminClient
from src.db.session import create_session_factory
from src.events_broker import EventBroker
from src.exceptions import SessionClosed, SessionNotFound
from src.gns3_ws_proxy import Gns3WsProxy
from src.history_listener_pg import HistoryPgListener
from src.middleware.request_id import RequestIDMiddleware
from src.observability.metrics import configure_metrics
from src.routers import (
    exec_router,
    health_router,
    history_router,
    projects_router,
    sessions_router,
    templates_router,
    ws_router,
)
from src.services.session_lifecycle import SessionService
from src.templates_bootstrap import ensure_lab_templates

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    admin = GNS3AdminClient(
        settings.gns3.url, settings.gns3.admin_user, settings.gns3.admin_password
    )
    await admin.authenticate()

    try:
        await ensure_lab_templates(admin)
    except Exception as exc:
        logger.error("Lab templates bootstrap failed, continuing: %s", exc)

    db_factory = create_session_factory(settings.database.async_url, settings.database.sql_echo)

    broker = EventBroker(redis_url=settings.redis.url)
    ws_proxy = Gns3WsProxy(
        broker,
        settings.gns3.url,
        admin,
        redis_url=settings.redis.url,
        db_factory=db_factory,
    )
    pg_dsn = settings.database.async_url.replace("+asyncpg", "")
    pg_listener = HistoryPgListener(pg_dsn, broker)

    from src.rbac_gate import RbacGate

    service = SessionService(
        admin_client=admin,
        gns3_url=settings.gns3.url,
        gns3_public_url=settings.gns3.public_url,
        ws_proxy=ws_proxy,
        # Redis-лок сериализует RBAC-записи и между репликами gns3-service.
        rbac_gate=RbacGate(redis_url=settings.redis.url),
    )

    # Перепривязать ws_proxy-форвардер ко всем активным сессиям после рестарта:
    # proxy state живёт в памяти, иначе события перестанут литься.
    from sqlalchemy import select

    from src.db.models import Session as SessionModel
    from src.db.models import SessionStatus
    async with db_factory() as db:
        active = await db.execute(
            select(SessionModel).where(SessionModel.status == SessionStatus.ACTIVE)
        )
        active_sessions = list(active.scalars())
    for s in active_sessions:
        await ws_proxy.start_project(s.gns3_project_id, str(s.id))
        logger.info(
            "startup: re-attached project %s -> session %s",
            s.gns3_project_id, s.id,
        )

    app.state.session_service = service
    app.state.db_factory = db_factory
    app.state.event_broker = broker
    app.state.ws_proxy = ws_proxy
    app.state.pg_listener = pg_listener

    await pg_listener.start()

    async def _state_cache_sweep():
        while True:
            try:
                await asyncio.sleep(60)
                removed = service.state_cache.sweep_stale(factor=10.0)
                if removed:
                    logger.info("state_cache: swept %d stale entries", removed)
            except asyncio.CancelledError:
                return
            except Exception:
                logger.exception("state_cache sweep failed")

    sweep_task = asyncio.create_task(_state_cache_sweep())

    yield
    sweep_task.cancel()
    try:
        await sweep_task
    except asyncio.CancelledError:
        pass
    await pg_listener.stop()
    await ws_proxy.stop_all()
    await broker.close()


app = FastAPI(title="GNS3 Service", version="0.1.0", lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)
configure_metrics(app)


@app.exception_handler(SessionNotFound)
async def _session_not_found_handler(request: Request, exc: SessionNotFound):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(SessionClosed)
async def _session_closed_handler(request: Request, exc: SessionClosed):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


app.include_router(sessions_router)
app.include_router(projects_router)
app.include_router(history_router)
app.include_router(health_router)
app.include_router(ws_router)
app.include_router(exec_router)
app.include_router(templates_router)


def main() -> None:
    uvicorn.run(app, host=settings.service.host, port=settings.service.port)


if __name__ == "__main__":
    main()
