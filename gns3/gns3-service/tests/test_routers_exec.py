"""Unit tests for POST /v1/exec/vtysh."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest

from src.config import settings
from src.routers.exec import router as exec_router


def _stub_response(status_code: int, payload: dict) -> MagicMock:
    """An httpx.Response with a bound request is not serializable without a mock."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


_VALID_TOKEN = "test-internal-token"


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(exec_router)
    # _admin is the attribute the router reaches for. service.* is not used.
    service = MagicMock()
    service._admin = AsyncMock()
    app.state.session_service = service
    return app


@pytest.fixture(autouse=True)
def _seed_internal_token(monkeypatch):
    """Guarantee a known token for verify_internal_token."""
    monkeypatch.setattr(settings.security, "internal_api_token", _VALID_TOKEN, raising=False)


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
    @autotest.num("3353")
    @autotest.external_id("02b9b88d-c8b0-42a4-9cd0-26351ce80ab9")
    @autotest.name("POST /v1/exec/vtysh: 403 without an Authorization header")
    async def test_02b9b88d_returns_403_without_authorization_header(self, client):
        with autotest.step("Act: POST vtysh without an Authorization header"):
            response = await client.post("/v1/exec/vtysh", json=VTYSH_BODY)

        with autotest.step("Assert: 403 missing bearer token"):
            assert response.status_code == 403
            assert response.json()["detail"] == "missing bearer token"

    @autotest.num("3354")
    @autotest.external_id("46a921ae-78c4-44c6-9334-44c70d43f95f")
    @autotest.name("POST /v1/exec/vtysh: 403 with an incorrect internal token")
    async def test_46a921ae_returns_403_with_wrong_token(self, client):
        with autotest.step("Act: POST vtysh with an incorrect internal token"):
            response = await client.post(
                "/v1/exec/vtysh",
                json=VTYSH_BODY,
                headers={"Authorization": "Bearer wrong-token"},
            )

        with autotest.step("Assert: 403 invalid internal token"):
            assert response.status_code == 403
            assert response.json()["detail"] == "invalid internal token"


class TestExecNodeTypeGuard:
    @autotest.num("3355")
    @autotest.external_id("62321ab2-d4ab-40ac-8df7-de43e52d10e3")
    @autotest.name("POST /v1/exec/vtysh: 400 when the target node is not docker")
    async def test_62321ab2_returns_400_when_node_is_not_docker(self, app, client):
        with autotest.step("Arrange: the target node reports a non-docker type"):
            admin = app.state.session_service._admin
            admin.request.return_value = _stub_response(
                200, {"node_type": "qemu", "properties": {}}
            )

        with autotest.step("Act: POST vtysh against that node"):
            response = await client.post(
                "/v1/exec/vtysh",
                json=VTYSH_BODY,
                headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
            )

        with autotest.step("Assert: 400, only docker nodes are supported"):
            assert response.status_code == 400
            assert "only docker nodes" in response.json()["detail"]


class TestExecHappyPath:
    @autotest.num("3356")
    @autotest.external_id("9d103297-62cf-497d-9162-b16b20f79194")
    @autotest.name("POST /v1/exec/vtysh: runs vtysh in the container and returns stdout")
    async def test_9d103297_runs_docker_exec_and_returns_stdout(self, app, client):
        with autotest.step("Arrange: a docker node and a subprocess stub returning stdout"):
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

        with autotest.step("Act: POST vtysh with the subprocess spawn mocked"):
            with patch(
                "src.routers.exec.asyncio.create_subprocess_exec",
                new=AsyncMock(return_value=proc),
            ) as mock_spawn:
                response = await client.post(
                    "/v1/exec/vtysh",
                    json=VTYSH_BODY,
                    headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
                )

        with autotest.step("Assert: 200 with stdout, and vtysh ran against the container"):
            assert response.status_code == 200
            assert response.json() == {
                "stdout": "R1#",
                "stderr": "",
                "exit_code": 0,
            }
            mock_spawn.assert_awaited_once()
            # Check that the command contains container_id and vtysh -c "..."
            args = mock_spawn.await_args.args
            assert "container-xyz" in args
            assert "vtysh" in args
            assert "show ip ospf neighbor" in args


class TestExecInfrastructureFailure:
    @autotest.num("3381")
    @autotest.external_id("a201ea0c-62fb-4960-8b2a-88d1fde062e9")
    @autotest.name("POST /v1/exec/vtysh: 503 when the docker daemon is unreachable")
    async def test_a201ea0c_returns_503_when_docker_daemon_unreachable(self, app, client):
        with autotest.step("Arrange: a docker node and a docker CLI that cannot reach the daemon"):
            admin = app.state.session_service._admin
            admin.request.return_value = _stub_response(
                200,
                {"node_type": "docker", "properties": {"container_id": "container-xyz"}},
            )
            proc = AsyncMock()
            proc.communicate.return_value = (
                b"",
                b"Cannot connect to the Docker daemon at unix:///var/run/docker.sock. "
                b"Is the docker daemon running?",
            )
            proc.returncode = 1

        with autotest.step("Act: POST vtysh with the subprocess spawn mocked"):
            with patch(
                "src.routers.exec.asyncio.create_subprocess_exec",
                new=AsyncMock(return_value=proc),
            ):
                response = await client.post(
                    "/v1/exec/vtysh",
                    json=VTYSH_BODY,
                    headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
                )

        with autotest.step("Assert: 503, not a 200 that looks like a failed check"):
            assert response.status_code == 503
            assert "docker exec failed before vtysh ran" in response.json()["detail"]

    @autotest.num("3382")
    @autotest.external_id("42d84653-fc10-4728-9164-a32a476b5f67")
    @autotest.name("POST /v1/exec/vtysh: 503 when docker exits with an infrastructure code")
    async def test_42d84653_returns_503_on_docker_infrastructure_exit_code(self, app, client):
        with autotest.step("Arrange: a docker node and docker exiting 125"):
            admin = app.state.session_service._admin
            admin.request.return_value = _stub_response(
                200,
                {"node_type": "docker", "properties": {"container_id": "container-xyz"}},
            )
            proc = AsyncMock()
            proc.communicate.return_value = (b"", b"docker: Error response from daemon.")
            proc.returncode = 125

        with autotest.step("Act: POST vtysh with the subprocess spawn mocked"):
            with patch(
                "src.routers.exec.asyncio.create_subprocess_exec",
                new=AsyncMock(return_value=proc),
            ):
                response = await client.post(
                    "/v1/exec/vtysh",
                    json=VTYSH_BODY,
                    headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
                )

        with autotest.step("Assert: 503 rather than a successful response"):
            assert response.status_code == 503

    @autotest.num("3383")
    @autotest.external_id("d8610feb-aa67-4788-bc80-517dc22070a7")
    @autotest.name("POST /v1/exec/vtysh: a failing vtysh command still returns 200")
    async def test_d8610feb_returns_200_when_vtysh_command_fails(self, app, client):
        with autotest.step("Arrange: a docker node and vtysh rejecting the command"):
            admin = app.state.session_service._admin
            admin.request.return_value = _stub_response(
                200,
                {"node_type": "docker", "properties": {"container_id": "container-xyz"}},
            )
            proc = AsyncMock()
            proc.communicate.return_value = (b"", b"% Unknown command")
            proc.returncode = 1

        with autotest.step("Act: POST vtysh with the subprocess spawn mocked"):
            with patch(
                "src.routers.exec.asyncio.create_subprocess_exec",
                new=AsyncMock(return_value=proc),
            ):
                response = await client.post(
                    "/v1/exec/vtysh",
                    json=VTYSH_BODY,
                    headers={"Authorization": f"Bearer {_VALID_TOKEN}"},
                )

        with autotest.step("Assert: 200 with the vtysh exit code preserved"):
            assert response.status_code == 200
            assert response.json()["exit_code"] == 1
            assert response.json()["stderr"] == "% Unknown command"
