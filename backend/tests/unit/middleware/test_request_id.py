"""RequestIDMiddleware: request_id flows into structlog contextvars and into the response header."""

import pytest
import structlog
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest

from core.middleware.request_id import RequestIDMiddleware

pytestmark = [pytest.mark.unit]


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/probe")
    async def probe():
        return dict(structlog.contextvars.get_contextvars())

    return app


@pytest.mark.asyncio
@autotest.num("3240")
@autotest.external_id("f45dcbd3-d76d-4fae-9dfd-87eb1edc28e1")
@autotest.name(
    "RequestIDMiddleware: binds request_id into structlog contextvars during the request"
)
async def test_f45dcbd3_request_id_bound_into_structlog_contextvars_during_request():
    with autotest.step("Arrange: app with RequestIDMiddleware and a probe route"):
        app = _build_app()

    with autotest.step("Act: GET /probe"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/probe")

    with autotest.step("Assert: 200 and contextvars carry the request_id, path and method"):
        assert resp.status_code == 200
        body = resp.json()
        assert "request_id" in body
        assert body["path"] == "/probe"
        assert body["method"] == "GET"


@pytest.mark.asyncio
@autotest.num("3241")
@autotest.external_id("e5bd2db4-f4b2-4022-aa47-6eb2dcc89b3d")
@autotest.name("RequestIDMiddleware: honors an incoming x-request-id header and echoes it back")
async def test_e5bd2db4_request_id_honors_incoming_header_and_echoes_it_in_response():
    with autotest.step("Arrange: app with RequestIDMiddleware and a probe route"):
        app = _build_app()

    with autotest.step("Act: GET /probe with an incoming x-request-id header"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/probe", headers={"x-request-id": "fixed-rid"})

    with autotest.step("Assert: response header and contextvars echo the incoming id"):
        assert resp.headers["x-request-id"] == "fixed-rid"
        assert resp.json()["request_id"] == "fixed-rid"


@pytest.mark.asyncio
@autotest.num("3242")
@autotest.external_id("508891c3-c860-4a60-9ca6-0ed86efee0db")
@autotest.name("RequestIDMiddleware: clears structlog contextvars after the request completes")
async def test_508891c3_contextvars_cleared_after_request_completes():
    with autotest.step("Arrange: app with RequestIDMiddleware and a probe route"):
        app = _build_app()

    with autotest.step("Act: GET /probe"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.get("/probe")

    with autotest.step("Assert: structlog contextvars are cleared after the request"):
        assert structlog.contextvars.get_contextvars() == {}
