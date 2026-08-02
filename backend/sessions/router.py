"""Aggregates the session endpoints under the prefix main.py mounts.

commands and queries each have a root "" route, and include_router rejects an
empty prefix plus an empty path, so those two are concatenated with
routes.extend. Using "/" instead would add a trailing slash and a 307.

Order matters only within queries.py, where `/queue-status` must precede the
catch-all `/{session_id}`: Starlette matches in registration order.
"""

from fastapi import APIRouter

from sessions.routers import commands, queries, ws

router = APIRouter()
router.routes.extend(commands.router.routes)
router.include_router(ws.router)
router.routes.extend(queries.router.routes)
