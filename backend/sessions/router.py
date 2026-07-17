"""Aggregator of session endpoints under the common prefix from main.py.

commands.router and queries.router each contain a handler with a root `""`
path (POST-launch and GET-list respectively). FastAPI forbids
include_router when both the include prefix and the sub-route path are
empty at the same time ("Prefix and path cannot be both empty") — so for
these we use routes.extend (a plain concatenation of the Route list, no
FastAPI validation). An explicit non-empty path (e.g. "/") would avoid
this, but it changes the resulting route (a trailing slash appears →
a 307 redirect instead of a direct 200), which violates the requirement of
an identical route table — so it's not used. ws.router has no root path,
so include_router works for it without workarounds.

Registration order only matters inside queries.py: there, the literal
`/queue-status` is registered before the catch-all `/{session_id}`,
otherwise the latter would swallow it (Starlette matches routes in
registration order). The order of commands/ws/queries relative to each
other doesn't affect matching (different methods or different path
segment counts), but is kept for readability.
"""

from fastapi import APIRouter

from sessions.routers import commands, queries, ws

router = APIRouter()
router.routes.extend(commands.router.routes)
router.include_router(ws.router)
router.routes.extend(queries.router.routes)
