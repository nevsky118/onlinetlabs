"""Locale-independent domain errors rendered at the HTTP boundary."""

from fastapi import Request
from fastapi.responses import JSONResponse

from i18n.catalog import t
from i18n.locale import negotiate


class LocalizedError(Exception):
    """A failure identified by a catalog key. Services raise it without knowing the locale."""

    def __init__(self, key: str, *, status_code: int = 400, **params: object):
        super().__init__(key)
        self.key = key
        self.status_code = status_code
        self.params = params


async def localized_error_handler(request: Request, exc: LocalizedError) -> JSONResponse:
    """Renders the error in the request locale; `code` stays stable for the frontend to branch on."""
    locale = negotiate(request.headers.get("x-locale"))
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": t(exc.key, locale, **exc.params), "code": exc.key},
    )
