"""Unit tests for the sessions REST router."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest

from src.exceptions import SessionNotFound
from src.models import SessionResponse
from src.routers.sessions import router as sessions_router


def _build_app() -> FastAPI:
    """Build a minimal application with the router and a 404 handler."""
    app = FastAPI()

    @app.exception_handler(SessionNotFound)
    async def _session_not_found_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    app.include_router(sessions_router)
    app.state.session_service = AsyncMock()
    app.state.db_factory = _StubDbFactory()
    return app


class _StubDbFactory:
    """Stand-in for the async session factory, yields an AsyncMock as a context manager."""

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
    @autotest.num("3357")
    @autotest.external_id("2b9ee5d6-9935-4b6e-bdeb-e6f21ba59eb8")
    @autotest.name("POST /sessions: 201 with the created session's id and username")
    async def test_2b9ee5d6_create_session_returns_201_and_payload(self, app, client):
        with autotest.step("Arrange: the session service returns a built session"):
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

        with autotest.step("Act: POST /sessions"):
            response = await client.post(
                "/sessions",
                json={"user_id": "user-42", "lab_template_project_id": "tpl-1"},
            )

        with autotest.step("Assert: 201 with the created session's id and username"):
            assert response.status_code == 201
            body = response.json()
            assert body["session_id"] == "11111111-1111-1111-1111-111111111111"
            assert body["gns3_username"] == "student_user42"
            app.state.session_service.create_session.assert_awaited_once()


class TestDeleteSession:
    @autotest.num("3358")
    @autotest.external_id("b8383f57-8e26-4cc1-aa00-58a8b850069f")
    @autotest.name("DELETE /sessions/{id}: 200 with a deleted status")
    async def test_b8383f57_delete_session_returns_status_deleted(self, app, client):
        with autotest.step("Arrange: the session service deletes without error"):
            app.state.session_service.delete_session.return_value = None
            sid = "22222222-2222-2222-2222-222222222222"

        with autotest.step("Act: DELETE the session"):
            response = await client.delete(f"/sessions/{sid}")

        with autotest.step("Assert: 200 with a deleted status"):
            assert response.status_code == 200
            assert response.json() == {"status": "deleted"}
            app.state.session_service.delete_session.assert_awaited_once()

    @autotest.num("3359")
    @autotest.external_id("40567105-fd60-46d5-a80b-0b10823ed302")
    @autotest.name("DELETE /sessions/{id}: 404 when the session is not found")
    async def test_40567105_delete_session_returns_404_when_not_found(self, app, client):
        with autotest.step("Arrange: the session service reports the session missing"):
            app.state.session_service.delete_session.side_effect = SessionNotFound(
                "session abc not found"
            )

        with autotest.step("Act: DELETE the missing session"):
            response = await client.delete("/sessions/33333333-3333-3333-3333-333333333333")

        with autotest.step("Assert: 404 with the not-found detail"):
            assert response.status_code == 404
            assert response.json() == {"detail": "session abc not found"}


class TestGetSessionState:
    @autotest.num("3360")
    @autotest.external_id("b1d47abc-ebe6-4d8d-a08e-cea3cab68eba")
    @autotest.name("GET /sessions/{id}/state: 502 on an unexpected error")
    async def test_b1d47abc_get_state_returns_502_on_unexpected_error(self, app, client):
        with autotest.step("Arrange: the session service raises an unexpected error"):
            # ValueError propagates → SessionNotFound → 404, otherwise → 502.
            app.state.session_service.get_state.side_effect = RuntimeError("gns3 down")
            sid = "44444444-4444-4444-4444-444444444444"

        with autotest.step("Act: GET the session state"):
            response = await client.get(f"/sessions/{sid}/state")

        with autotest.step("Assert: 502 GNS3 unreachable"):
            assert response.status_code == 502
            assert response.json() == {"detail": "GNS3 unreachable"}
