"""X-Request-ID middleware: read incoming or generate UUID, bind to structlog contextvars."""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_log = structlog.get_logger("request")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware, проставляющий X-Request-ID для каждого запроса и логирующий его обработку."""

    async def dispatch(self, request: Request, call_next):
        """Привязывает request_id к structlog-контексту, обрабатывает запрос и возвращает заголовок в ответе."""
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        # structlog contextvars живут на task-локальном уровне, но воркер
        # переиспользует одну и ту же задачу для последующих запросов.
        # Чистим явно, чтобы между запросами не утекали user_id и session_id.
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
