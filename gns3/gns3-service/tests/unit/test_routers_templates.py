"""Unit tests for POST /v1/templates/{lab}/build."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in

from src.config import settings
from src.routers.templates import router as templates_router

pytestmark = [pytest.mark.unit]

_VALID_TOKEN = "test-internal-token"
_KNOWN_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(templates_router)
    return app


@pytest.fixture(autouse=True)
def _seed_internal_token(monkeypatch):
    monkeypatch.setattr(settings.security, "internal_api_token", _VALID_TOKEN, raising=False)


@pytest.fixture
def app():
    return _build_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestTemplateAuth:
    @autotest.num("3361")
    @autotest.external_id("b495b994-0bf1-4091-b0f2-5cd0f8626c2a")
    @autotest.name("POST /v1/templates/{lab}/build: 403 without a token")
    async def test_b495b994_missing_token_returns_403(self, client):
        with autotest.step("Act: POST a template build without a token"):
            response = await client.post("/v1/templates/lan-static-ip/build")

        with autotest.step("Assert: 403"):
            assert_equal(response.status_code, 403, "status code")

    @autotest.num("3362")
    @autotest.external_id("f0ed845f-cde9-45cb-b01c-243f89a4b786")
    @autotest.name("POST /v1/templates/{lab}/build: 403 with the wrong token")
    async def test_f0ed845f_wrong_token_returns_403(self, client):
        with autotest.step("Act: POST a template build with the wrong token"):
            response = await client.post(
                "/v1/templates/lan-static-ip/build",
                headers={"Authorization": "Bearer wrong"},
            )

        with autotest.step("Assert: 403"):
            assert_equal(response.status_code, 403, "status code")


class TestTemplateLabLookup:
    @autotest.num("3363")
    @autotest.external_id("40d251ff-4842-4e42-893f-05cc8c86ab97")
    @autotest.name("POST /v1/templates/{lab}/build: 404 for an unknown lab")
    async def test_40d251ff_unknown_lab_returns_404(self, client):
        with autotest.step("Act: POST a build for an unknown lab"):
            response = await client.post(
                "/v1/templates/nope/build",
                headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
            )

        with autotest.step("Assert: 404 unknown lab"):
            assert_equal(response.status_code, 404, "status code")
            assert_in("Unknown lab", response.json()["detail"], "'Unknown lab'")


class TestTemplateBuildHappyPath:
    @autotest.num("3364")
    @autotest.external_id("0d25cea6-9c09-4576-9a88-e280ce987068")
    @autotest.name("POST /v1/templates/{lab}/build: 200 with the built template's project id")
    async def test_0d25cea6_returns_template_project_id(self, client):
        with autotest.step("Act: POST a build with _run_build mocked to succeed"):
            with patch(
                "src.routers.templates._run_build",
                new=AsyncMock(return_value=_KNOWN_UUID),
            ):
                response = await client.post(
                    "/v1/templates/lan-static-ip/build",
                    headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
                )

        with autotest.step("Assert: 200 with the built template's project id"):
            assert_equal(response.status_code, 200, "status code")
            assert_equal(response.json(), {"template_project_id": _KNOWN_UUID}, "json")
