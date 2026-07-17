"""RequestIDMiddleware: request_id flows into structlog contextvars and into the response header."""

import pytest
import structlog
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from middleware.request_id import RequestIDMiddleware

pytestmark = [pytest.mark.unit]


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/probe")
    async def probe():
        return dict(structlog.contextvars.get_contextvars())

    return app


@pytest.mark.asyncio
async def test_request_id_bound_into_structlog_contextvars_during_request():
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/probe")
    assert resp.status_code == 200
    body = resp.json()
    assert "request_id" in body
    assert body["path"] == "/probe"
    assert body["method"] == "GET"


@pytest.mark.asyncio
async def test_request_id_honors_incoming_header_and_echoes_it_in_response():
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/probe", headers={"x-request-id": "fixed-rid"})
    assert resp.headers["x-request-id"] == "fixed-rid"
    assert resp.json()["request_id"] == "fixed-rid"


@pytest.mark.asyncio
async def test_contextvars_cleared_after_request_completes():
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/probe")
    assert structlog.contextvars.get_contextvars() == {}
