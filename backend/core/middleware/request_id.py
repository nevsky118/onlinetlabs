"""X-Request-ID middleware: read incoming or generate UUID, bind to structlog contextvars."""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_log = structlog.get_logger("request")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that stamps X-Request-ID on every request and logs its handling."""

    async def dispatch(self, request: Request, call_next):
        """Binds request_id to the structlog context, handles the request, and returns the header in the response."""
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        # structlog contextvars are task-local, but the worker reuses the same task across
        # requests, so clear explicitly or user_id/session_id leak between them.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=rid, path=request.url.path, method=request.method
        )
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            _log.info(
                "request_handled",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=duration_ms,
            )
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers["x-request-id"] = rid
        return response
