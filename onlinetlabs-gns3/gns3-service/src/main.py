# FastAPI приложение gns3-service.

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from src.router import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    listener = getattr(app.state, "history_listener", None)
    if listener:
        await listener.start()
    yield
    if listener:
        await listener.stop()


def create_app(
    session_service: Any = None,
    db_factory: Any = None,
    history_listener: Any = None,
) -> FastAPI:
    application = FastAPI(title="GNS3 Service", version="0.1.0", lifespan=lifespan)
    application.state.session_service = session_service
    application.state.db_factory = db_factory
    application.state.history_listener = history_listener
    application.include_router(router)
    return application


app = create_app()


def main() -> None:
    import asyncio
    from urllib.parse import urlparse, urlunparse

    import uvicorn

    from src.config import settings
    from src.db.session import create_session_factory
    from src.gns3_admin_client import GNS3AdminClient
    from src.history import HistoryListener
    from src.service import SessionService

    admin = GNS3AdminClient(
        settings.gns3.url, settings.gns3.admin_user, settings.gns3.admin_password
    )
    asyncio.new_event_loop().run_until_complete(admin.authenticate())

    db_factory = create_session_factory(settings.database.async_url, settings.database.sql_echo)
    service = SessionService(admin_client=admin, gns3_url=settings.gns3.url)

    parsed = urlparse(settings.gns3.url)
    ws_scheme = "wss" if parsed.scheme == "https" else "ws"
    ws_url = urlunparse((ws_scheme, parsed.netloc, "/v3/notifications", "", "", ""))
    listener = HistoryListener(ws_url, admin.token, db_factory)

    application = create_app(
        session_service=service, db_factory=db_factory, history_listener=listener
    )
    uvicorn.run(application, host=settings.service.host, port=settings.service.port)


if __name__ == "__main__":
    main()
