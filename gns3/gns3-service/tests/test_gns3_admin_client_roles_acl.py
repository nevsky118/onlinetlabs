"""Unit-тесты GNS3AdminClient RolesMixin и AclMixin."""

import httpx
import pytest
import respx
from httpx import Response

from src.gns3_admin_client import GNS3AdminClient


class TestGns3AdminClientRoles:
    """Unit-тесты управления ролями через HTTP-обёртку."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3-server:3080", "admin", "pass")
        client.set_admin_token("fake")
        return client

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_role_returns_payload(self, admin_client):
        respx.post("http://gns3-server:3080/v3/access/roles").mock(
            return_value=Response(201, json={"role_id": "r1", "name": "Student", "is_builtin": False}),
        )
        result = await admin_client.create_role(name="Student")
        assert result["role_id"] == "r1"
        assert result["name"] == "Student"

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_role_raises_on_409(self, admin_client):
        respx.post("http://gns3-server:3080/v3/access/roles").mock(
            return_value=Response(409, json={"message": "duplicate"}),
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await admin_client.create_role(name="Student")
        assert exc_info.value.response.status_code == 409

    @pytest.mark.asyncio
    @respx.mock
    async def test_delete_role_ok(self, admin_client):
        route = respx.delete("http://gns3-server:3080/v3/access/roles/r1").mock(
            return_value=Response(204),
        )
        await admin_client.delete_role("r1")
        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_delete_role_raises_on_404(self, admin_client):
        respx.delete("http://gns3-server:3080/v3/access/roles/missing").mock(
            return_value=Response(404, json={"message": "not found"}),
        )
        with pytest.raises(httpx.HTTPStatusError):
            await admin_client.delete_role("missing")

    @pytest.mark.asyncio
    @respx.mock
    async def test_assign_role_to_user_ok(self, admin_client):
        route = respx.put("http://gns3-server:3080/v3/access/users/u1").mock(
            return_value=Response(200, json={"user_id": "u1"}),
        )
        await admin_client.assign_role_to_user("u1", "r1")
        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_assign_role_to_user_raises_on_404(self, admin_client):
        respx.put("http://gns3-server:3080/v3/access/users/missing").mock(
            return_value=Response(404, json={"message": "not found"}),
        )
        with pytest.raises(httpx.HTTPStatusError):
            await admin_client.assign_role_to_user("missing", "r1")

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_builtin_role_returns_match_and_caches(self, admin_client):
        route = respx.get("http://gns3-server:3080/v3/access/roles").mock(
            return_value=Response(200, json=[
                {"role_id": "r1", "name": "User", "is_builtin": True},
                {"role_id": "r2", "name": "Administrator", "is_builtin": True},
                {"role_id": "r3", "name": "Custom", "is_builtin": False},
            ]),
        )
        result = await admin_client.get_builtin_role("User")
        assert result["role_id"] == "r1"
        # Повторный вызов — должен вернуться из кеша без HTTP-запроса.
        result_cached = await admin_client.get_builtin_role("User")
        assert result_cached["role_id"] == "r1"
        assert route.call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_builtin_role_raises_when_missing(self, admin_client):
        respx.get("http://gns3-server:3080/v3/access/roles").mock(
            return_value=Response(200, json=[
                {"role_id": "r1", "name": "User", "is_builtin": True},
            ]),
        )
        with pytest.raises(ValueError, match="Ghost"):
            await admin_client.get_builtin_role("Ghost")


class TestGns3AdminClientAcl:
    """Unit-тесты управления ACL через HTTP-обёртку."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3-server:3080", "admin", "pass")
        client.set_admin_token("fake")
        return client

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_acl_returns_payload(self, admin_client):
        respx.post("http://gns3-server:3080/v3/access/acl").mock(
            return_value=Response(201, json={
                "ace_id": "a1",
                "path": "/projects/p1",
                "role_id": "r1",
                "user_id": "u1",
                "ace_type": "user",
                "allowed": True,
            }),
        )
        result = await admin_client.create_acl(
            path="/projects/p1", role_id="r1", user_id="u1",
        )
        assert result["ace_id"] == "a1"
        assert result["allowed"] is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_acl_raises_on_409(self, admin_client):
        respx.post("http://gns3-server:3080/v3/access/acl").mock(
            return_value=Response(409, json={"message": "duplicate"}),
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await admin_client.create_acl(
                path="/projects/p1", role_id="r1", user_id="u1",
            )
        assert exc_info.value.response.status_code == 409
