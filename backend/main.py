import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

import api
from agents.orchestrator.agent import Orchestrator
from clients.gns3 import Gns3ServiceClient
from clients.mcp import MCPClient
from config import settings
from i18n import LocalizedError, localized_error_handler, negotiate, t, validate_catalogs
from kit.db import async_session
from kit.middleware import RequestIDMiddleware
from kit.rate_limit import limiter
from kit.redis import redis_client
from labs.service import log_lab_problems
from observability.activity import AgentActivityLog
from observability.bootstrap import bootstrap
from observability.metrics import configure_metrics
from sessions.monitor_registry import SessionMonitorRegistry
from sessions.queue import SessionQueueService
from sessions.services.proxy import _BULK_GNS3_SEMAPHORE
from sessions.state_cache import StateCache
from sessions.ws import WebSocketGateway, close_all_connections
from worker.idle_reclaim import idle_reclaim_loop
from worker.reaper import session_reaper_loop
from worker.restore import restore_session_monitors
from worker.retention import retention_loop

bootstrap()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Brings up app dependencies, puts them in app.state and shuts them down cleanly on stop."""
    # Fail at boot, not at a student's first message.
    validate_catalogs()

    mcp_client = MCPClient(settings.mcp.server_url)
    gateway = WebSocketGateway()
    orchestrator = Orchestrator(settings)
    gns3_client = Gns3ServiceClient(
        settings.gns3.service_url,
        internal_token=settings.security.internal_api_token,
    )
    activity_log = AgentActivityLog(async_session, settings.observability.retention_per_session)
    await activity_log.start()
    monitor_registry = SessionMonitorRegistry(
        config=settings,
        mcp_client=mcp_client,
        db_factory=async_session,
        orchestrator=orchestrator,
        gateway=gateway,
        activity_log=activity_log,
        gns3_client=gns3_client,
    )
    redis = redis_client()

    app.state.mcp_client = mcp_client
    app.state.gateway = gateway
    app.state.orchestrator = orchestrator
    app.state.gns3_client = gns3_client
    app.state.monitor_registry = monitor_registry
    app.state.activity_log = activity_log
    app.state.state_cache = StateCache(redis, ttl_seconds=5)
    app.state.session_queue = SessionQueueService()
    app.state.bulk_gns3_semaphore = _BULK_GNS3_SEMAPHORE

    tasks = [
        asyncio.create_task(idle_reclaim_loop(gns3_client)),
        asyncio.create_task(session_reaper_loop(gns3_client, monitor_registry)),
        asyncio.create_task(retention_loop()),
        asyncio.create_task(log_lab_problems()),
        asyncio.create_task(restore_session_monitors(monitor_registry)),
    ]
    yield
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    await close_all_connections()
    await activity_log.stop()
    await redis.close()
    await monitor_registry.stop_all()
    await gns3_client.close()
    await mcp_client.close()


app = FastAPI(lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(LocalizedError, localized_error_handler)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Returns 429 with a clear message when the request rate limit is exceeded."""
    locale = negotiate(request.headers.get("x-locale"))
    return JSONResponse(
        status_code=429,
        content={"detail": t("error.rate_limit", locale), "code": "error.rate_limit"},
    )


app.add_middleware(RequestIDMiddleware)

configure_metrics(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.api.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.register(app)
