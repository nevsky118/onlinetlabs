import asyncio
import logging
import os
from contextlib import asynccontextmanager

import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from config import settings
from observability.logging import configure_logging
from observability.metrics import configure_metrics
from observability.sentry import configure_sentry

configure_logging("backend", level=getattr(getattr(settings, "log", None), "log_level", "INFO"))
configure_sentry("backend", environment=os.getenv("ENVIRONMENT", "dev"))

from agents.orchestrator.agent import Orchestrator
from analytics.router import router as analytics_router
from auth.router import router as auth_router
from chat.router import router as chat_router
from courses.router import router as courses_router
from db.session import async_session
from experiment.router import router as experiment_router
from gns3_service_client import Gns3ServiceClient
from instructor.router import router as instructor_router
from labs.router import router as labs_router
from mcp_client.client import MCPClient
from middleware.request_id import RequestIDMiddleware
from observability.activity import AgentActivityLog
from progress.router import router as progress_router
from rate_limit import limiter
from sessions.idle_reclaim import idle_reclaim_loop
from sessions.monitor_registry import SessionMonitorRegistry
from sessions.queue import SessionQueueService
from sessions.router import router as sessions_router
from sessions.routers.agent_activity import router as agent_activity_router
from sessions.services.proxy import _BULK_GNS3_SEMAPHORE
from sessions.state_cache import StateCache
from sessions.ws import WebSocketGateway, close_all_connections
from validation.router import router as validation_router
from validation.runs_router import router as validation_runs_router

logger = logging.getLogger(__name__)


async def _restore_session_monitors(monitor_registry: SessionMonitorRegistry) -> None:
    """Перезапускает SessionMonitor для активных сессий после рестарта backend.

    Реестр мониторов живёт в памяти (app.state) и теряется при перезапуске
    контейнера — без восстановления активные сессии остаются без проактивных
    интервенций до повторного launch.
    """
    from sqlalchemy import select

    from models.session import LearningSession
    from sessions.context import build_session_context

    try:
        async with async_session() as db:
            result = await db.execute(
                select(LearningSession).where(LearningSession.status == "active")
            )
            sessions = result.scalars().all()
    except Exception:
        logger.warning("Не удалось загрузить активные сессии для мониторинга", exc_info=True)
        return

    for session in sessions:
        try:
            ctx = build_session_context(session)
            await monitor_registry.start(session.id, session.user_id, session.lab_slug, ctx)
        except Exception:
            logger.warning(
                "Не удалось восстановить SessionMonitor для %s", session.id, exc_info=True
            )
    if sessions:
        logger.info("Восстановлено мониторов сессий: %d", len(sessions))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Поднимает зависимости приложения, кладёт их в app.state и корректно гасит при остановке.

    Создаёт MCP-клиент, шлюз, оркестратор, клиенты и фоновые задачи на старте
    и закрывает соединения и задачи на выходе.
    """
    mcp_client = MCPClient(settings.mcp.server_url)
    gateway = WebSocketGateway()
    orchestrator = Orchestrator(settings, mcp_client=mcp_client)
    gns3_client = Gns3ServiceClient(
        settings.gns3.service_url,
        internal_token=settings.security.internal_api_token,
    )
    activity_log = AgentActivityLog(async_session, settings.observability.retention_per_session)
    monitor_registry = SessionMonitorRegistry(
        config=settings,
        mcp_client=mcp_client,
        db_factory=async_session,
        orchestrator=orchestrator,
        gateway=gateway,
        activity_log=activity_log,
        gns3_client=gns3_client,
    )
    redis_url = settings.redis.url
    redis_client = aioredis.from_url(redis_url, decode_responses=True)
    state_cache = StateCache(redis_client, ttl_seconds=5)
    session_queue = SessionQueueService()
    app.state.mcp_client = mcp_client
    app.state.gateway = gateway
    app.state.orchestrator = orchestrator
    app.state.gns3_client = gns3_client
    app.state.monitor_registry = monitor_registry
    app.state.activity_log = activity_log
    app.state.state_cache = state_cache
    app.state.session_queue = session_queue
    app.state.bulk_gns3_semaphore = _BULK_GNS3_SEMAPHORE
    reclaim_task = asyncio.create_task(idle_reclaim_loop(gns3_client))
    restore_task = asyncio.create_task(_restore_session_monitors(monitor_registry))
    yield
    restore_task.cancel()
    try:
        await restore_task
    except asyncio.CancelledError:
        pass
    reclaim_task.cancel()
    try:
        await reclaim_task
    except asyncio.CancelledError:
        pass
    await close_all_connections()
    await redis_client.close()
    await monitor_registry.stop_all()
    await gns3_client.close()


app = FastAPI(lifespan=lifespan)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Возвращает 429 с понятным сообщением при превышении лимита запросов."""
    return JSONResponse(status_code=429, content={"detail": "Слишком много запросов, попробуй чуть позже"})


app.add_middleware(RequestIDMiddleware)

configure_metrics(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.api.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(courses_router, prefix="/courses", tags=["courses"])
app.include_router(labs_router, prefix="/labs", tags=["labs"])
app.include_router(progress_router, prefix="/users/me/progress", tags=["progress"])
app.include_router(instructor_router, prefix="/instructor", tags=["instructor"])
app.include_router(sessions_router, prefix="/users/me/sessions", tags=["sessions"])
app.include_router(experiment_router, prefix="/experiment", tags=["experiment"])
app.include_router(validation_router, prefix="/labs", tags=["validation"])
app.include_router(validation_runs_router, prefix="/sessions", tags=["validation"])
app.include_router(agent_activity_router, prefix="/sessions", tags=["observability"])
app.include_router(chat_router, tags=["chat"])


@app.get("/")
def root():
    """Корневой эндпоинт с приветственным сообщением."""
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    """Мгновенная проверка живости процесса для k8s liveness. Без внешних вызовов."""
    return {"status": "ok"}


@app.get("/health/deep")
async def health_deep():
    """Глубокая проверка зависимостей для readiness probe и алертов.

    Опрашивает БД, Redis и gns3-service. На 503 k8s выводит pod из ротации,
    но не убивает его, чтобы временная просадка зависимости не каскадила.
    """
    checks: dict[str, str] = {}
    overall_ok = True

    try:
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {exc.__class__.__name__}"
        overall_ok = False

    try:
        client = aioredis.from_url(settings.redis.url)
        try:
            await client.ping()
        finally:
            await client.aclose()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc.__class__.__name__}"
        overall_ok = False

    try:
        async with httpx.AsyncClient(timeout=2.0) as c:
            r = await c.get(f"{settings.gns3.service_url}/health")
            r.raise_for_status()
        checks["gns3_service"] = "ok"
    except Exception as exc:
        checks["gns3_service"] = f"error: {exc.__class__.__name__}"
        overall_ok = False

    return JSONResponse(
        content={"status": "ok" if overall_ok else "degraded", "checks": checks},
        status_code=200 if overall_ok else 503,
    )
