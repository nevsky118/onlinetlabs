"""Unit-тесты REST-роутера sessions."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from src.exceptions import SessionNotFound
from src.models import SessionResponse
from src.routers.sessions import router as sessions_router


def _build_app() -> FastAPI:
    """Сконструировать минимальное приложение с роутером и handler'ом 404."""
    app = FastAPI()

    @app.exception_handler(SessionNotFound)
    async def _session_not_found_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    app.include_router(sessions_router)
    app.state.session_service = AsyncMock()
    app.state.db_factory = _StubDbFactory()
    return app


class _StubDbFactory:
    """Имитация фабрики async-сессий: yield-ит AsyncMock как контекст-менеджер."""

    def __call__(self):
        return _StubDbCtx()


class _StubDbCtx:
    async def __aenter__(self):
        return AsyncMock()

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def app():
    return _build_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestCreateSession:
    async def test_create_session_returns_201_and_payload(self, app, client):
        payload = SessionResponse(
            session_id="11111111-1111-1111-1111-111111111111",
            gns3_jwt="jwt-token",
            project_id="proj-1",
            gns3_user_id="user-1",
            gns3_username="student_user42",
            gns3_password="secret",
            gns3_url="http://gns3:3080",
            gns3_deep_url="http://gns3:3080/static/web-ui/controller/1/project/proj-1",
        )
        app.state.session_service.create_session.return_value = payload

        response = await client.post(
            "/sessions",
            json={"user_id": "user-42", "lab_template_project_id": "tpl-1"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["session_id"] == "11111111-1111-1111-1111-111111111111"
        assert body["gns3_username"] == "student_user42"
        app.state.session_service.create_session.assert_awaited_once()


class TestDeleteSession:
    async def test_delete_session_returns_status_deleted(self, app, client):
        app.state.session_service.delete_session.return_value = None
        sid = "22222222-2222-2222-2222-222222222222"

        response = await client.delete(f"/sessions/{sid}")

        assert response.status_code == 200
        assert response.json() == {"status": "deleted"}
        app.state.session_service.delete_session.assert_awaited_once()

    async def test_delete_session_returns_404_when_not_found(self, app, client):
        app.state.session_service.delete_session.side_effect = SessionNotFound(
            "session abc not found"
        )

        response = await client.delete("/sessions/33333333-3333-3333-3333-333333333333")

        assert response.status_code == 404
        assert response.json() == {"detail": "session abc not found"}


class TestGetSessionState:
    async def test_get_state_returns_502_on_unexpected_error(self, app, client):
        # ValueError пробрасывается → SessionNotFound → 404, иначе → 502.
        app.state.session_service.get_state.side_effect = RuntimeError("gns3 down")
        sid = "44444444-4444-4444-4444-444444444444"

        response = await client.get(f"/sessions/{sid}/state")

        assert response.status_code == 502
        assert response.json() == {"detail": "GNS3 unreachable"}
