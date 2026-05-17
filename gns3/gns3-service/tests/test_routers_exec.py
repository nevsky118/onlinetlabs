"""Unit-тесты POST /v1/exec/vtysh."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.config import settings
from src.routers.exec import router as exec_router


def _stub_response(status_code: int, payload: dict) -> MagicMock:
    """httpx.Response с привязанным request не сериализуется без мока."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


_VALID_TOKEN = "test-internal-token"


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(exec_router)
    # _admin — атрибут, к которому обращается роутер. service.* не используется.
    service = MagicMock()
    service._admin = AsyncMock()
    app.state.session_service = service
    return app


@pytest.fixture(autouse=True)
def _seed_internal_token(monkeypatch):
    """Гарантируем известный токен для verify_internal_token."""
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


VTYSH_BODY = {
    "project_id": "proj-1",
    "node_id": "node-1",
    "command": "show ip ospf neighbor",
}


class TestExecAuth:
    async def test_returns_403_without_authorization_header(self, client):
        response = await client.post("/v1/exec/vtysh", json=VTYSH_BODY)
        assert response.status_code == 403
        assert response.json()["detail"] == "missing bearer token"

    async def test_returns_403_with_wrong_token(self, client):
        response = await client.post(
            "/v1/exec/vtysh",
            json=VTYSH_BODY,
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "invalid internal token"


class TestExecNodeTypeGuard:
    async def test_returns_400_when_node_is_not_docker(self, app, client):
        admin = app.state.session_service._admin
        admin.request.return_value = _stub_response(
            200, {"node_type": "qemu", "properties": {}}
        )

        response = await client.post(
            "/v1/exec/vtysh",
            json=VTYSH_BODY,
            headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
        )

        assert response.status_code == 400
        assert "only docker nodes" in response.json()["detail"]


class TestExecHappyPath:
    async def test_runs_docker_exec_and_returns_stdout(self, app, client):
        admin = app.state.session_service._admin
        admin.request.return_value = _stub_response(
            200,
            {
                "node_type": "docker",
                "properties": {"container_id": "container-xyz"},
            },
        )

        proc = AsyncMock()
        proc.communicate.return_value = (b"R1#", b"")
        proc.returncode = 0

        with patch(
            "src.routers.exec.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ) as mock_spawn:
            response = await client.post(
                "/v1/exec/vtysh",
                json=VTYSH_BODY,
                headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
            )

        assert response.status_code == 200
        assert response.json() == {
            "stdout": "R1#",
            "stderr": "",
            "exit_code": 0,
        }
        mock_spawn.assert_awaited_once()
        # Проверим что в команде есть container_id и vtysh -c "..."
        args = mock_spawn.await_args.args
        assert "container-xyz" in args
        assert "vtysh" in args
        assert "show ip ospf neighbor" in args
