import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from httpx import ASGITransport, AsyncClient
from tests.report import autotests

pytestmark = [pytest.mark.integration, pytest.mark.router]


@pytest.fixture
def mock_service():
    from src.models import SessionResponse
    svc = AsyncMock()
    svc.create_session.return_value = SessionResponse(
        session_id="sid-1", gns3_jwt="jwt", project_id="pid",
        gns3_user_id="uid", gns3_username="student-abc",
        gns3_password="pass123", gns3_url="http://gns3:3080",
    )
    return svc


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
async def test_client(mock_service, mock_db):
    from src.main import create_app

    @asynccontextmanager
    async def _fake_factory():
        yield mock_db

    app = create_app(session_service=mock_service, db_factory=_fake_factory)
    # Set state directly — ASGITransport may not trigger lifespan
    app.state.session_service = mock_service
    app.state.db_factory = _fake_factory
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestRouter:
    @autotests.num("460")
    @autotests.external_id("b1c2d3e4-0001-4bbb-cccc-460000000001")
    @autotests.name("GNS3 Service Router: POST /sessions создаёт сессию")
    async def test_create_session(self, test_client, mock_service):
        response = await test_client.post("/sessions", json={
            "user_id": "student-1", "lab_template_project_id": "template-pid",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["gns3_jwt"] == "jwt"
        assert data["gns3_username"] == "student-abc"

    @autotests.num("461")
    @autotests.external_id("b1c2d3e4-0002-4bbb-cccc-461000000001")
    @autotests.name("GNS3 Service Router: DELETE /sessions/{id} удаляет")
    async def test_delete_session(self, test_client, mock_service):
        response = await test_client.delete("/sessions/sid-1")
        assert response.status_code == 200
        mock_service.delete_session.assert_called_once()

    @autotests.num("462")
    @autotests.external_id("b1c2d3e4-0003-4bbb-cccc-462000000001")
    @autotests.name("GNS3 Service Router: GET /history/{id}/actions возвращает список")
    async def test_get_history_actions(self, test_client, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        response = await test_client.get("/history/00000000-0000-0000-0000-000000000001/actions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
