"""REST- и WebSocket-роутеры gns3-service."""

from .exec import router as exec_router
from .health import router as health_router
from .history import router as history_router
from .projects import router as projects_router
from .sessions import router as sessions_router
from .ws import router as ws_router

__all__ = [
    "exec_router",
    "health_router",
    "history_router",
    "projects_router",
    "sessions_router",
    "ws_router",
]
