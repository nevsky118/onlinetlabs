"""Unit-тесты POST /v1/templates/{lab}/build."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.config import settings
from src.routers.templates import router as templates_router

_VALID_TOKEN = "test-internal-token"
_KNOWN_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(templates_router)
    return app


@pytest.fixture(autouse=True)
def _seed_internal_token(monkeypatch):
    monkeypatch.setattr(
        settings.security, "internal_api_token", _VALID_TOKEN, raising=False
    )


@pytest.fixture
def app():
    return _build_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestTemplateAuth:
    async def test_missing_token_returns_403(self, client):
        response = await client.post("/v1/templates/lan-static-ip/build")
        assert response.status_code == 403

    async def test_wrong_token_returns_403(self, client):
        response = await client.post(
            "/v1/templates/lan-static-ip/build",
            headers={"Authorization": "Bearer wrong"},
        )
        assert response.status_code == 403


class TestTemplateLabLookup:
    async def test_unknown_lab_returns_404(self, client):
        response = await client.post(
            "/v1/templates/nope/build",
            headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
        )
        assert response.status_code == 404
        assert "Unknown lab" in response.json()["detail"]


class TestTemplateBuildHappyPath:
    async def test_returns_template_project_id(self, client):
        with patch(
            "src.routers.templates._run_build",
            new=AsyncMock(return_value=_KNOWN_UUID),
        ):
            response = await client.post(
                "/v1/templates/lan-static-ip/build",
                headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
            )

        assert response.status_code == 200
        assert response.json() == {"template_project_id": _KNOWN_UUID}
