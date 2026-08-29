"""Joins the session endpoints into one router for api.py.

commands and queries each carry their own prefix and each has a root "" route,
which include_router refuses to re-prefix, so the two are concatenated with
routes.extend. That copies routes verbatim, prefix and dependencies included.

Order matters within queries.py, where `/queue-status` must precede the
catch-all `/{session_id}`: Starlette matches in registration order.

The websocket routes are exported separately. They authenticate from a query
token, and the HTTP-only liveness dependency cannot bind its Request on a
websocket, so ws.py declares no dependencies.
"""

from fastapi import APIRouter

from sessions.routers import commands, queries
from sessions.routers.ws import router as ws_router

router = APIRouter()
router.routes.extend(commands.router.routes)
router.routes.extend(queries.router.routes)

__all__ = ["router", "ws_router"]
