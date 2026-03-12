# FastAPI приложение gns3-service.

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config import settings
from src.db.session import create_session_factory
from src.gns3_admin_client import GNS3AdminClient
from src.history import HistoryListener
from src.router import router
from src.service import SessionService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    admin = GNS3AdminClient(
        settings.gns3.url, settings.gns3.admin_user, settings.gns3.admin_password
    )
    await admin.authenticate()

    db_factory = create_session_factory(settings.database.async_url, settings.database.sql_echo)
    service = SessionService(admin_client=admin, gns3_url=settings.gns3.url)
    listener = HistoryListener(settings.gns3.url, admin.token, db_factory)

    app.state.session_service = service
    app.state.db_factory = db_factory
    app.state.history_listener = listener

    await listener.start()
    yield
    await listener.stop()


app = FastAPI(title="GNS3 Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)


def main() -> None:
    uvicorn.run(app, host=settings.service.host, port=settings.service.port)


if __name__ == "__main__":
    main()
