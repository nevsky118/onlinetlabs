"""Unit-тесты GNS3AdminClient UsersMixin."""

import httpx
import pytest
import respx
from httpx import Response

from src.clients.admin import GNS3AdminClient


class TestGns3AdminClientUsers:
    """Unit-тесты управления пользователями через HTTP-обёртку."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3-server:3080", "admin", "pass")
        client.set_admin_token("fake")
        return client

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_user_returns_payload(self, admin_client, gns3_user):
        respx.post("http://gns3-server:3080/v3/access/users").mock(
            return_value=Response(201, json=gns3_user(user_id="u1", username="student-1")),
        )
        result = await admin_client.create_user(username="student-1", password="x")
        assert result["user_id"] == "u1"
        assert result["username"] == "student-1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_user_raises_on_409(self, admin_client):
        respx.post("http://gns3-server:3080/v3/access/users").mock(
            return_value=Response(409, json={"message": "already registered"}),
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await admin_client.create_user(username="student-1", password="x")
        assert exc_info.value.response.status_code == 409

    @pytest.mark.asyncio
    @respx.mock
    async def test_update_user_password_ok(self, admin_client):
        route = respx.put("http://gns3-server:3080/v3/access/users/u1").mock(
            return_value=Response(200, json={"user_id": "u1"}),
        )
        await admin_client.update_user_password("u1", "new-pass")
        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_update_user_password_raises_on_404(self, admin_client):
        respx.put("http://gns3-server:3080/v3/access/users/missing").mock(
            return_value=Response(404, json={"message": "not found"}),
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await admin_client.update_user_password("missing", "new-pass")
        assert exc_info.value.response.status_code == 404

    @pytest.mark.asyncio
    @respx.mock
    async def test_delete_user_ok(self, admin_client):
        route = respx.delete("http://gns3-server:3080/v3/access/users/u1").mock(
            return_value=Response(204),
        )
        await admin_client.delete_user("u1")
        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_delete_user_raises_on_404(self, admin_client):
        respx.delete("http://gns3-server:3080/v3/access/users/missing").mock(
            return_value=Response(404, json={"message": "not found"}),
        )
        with pytest.raises(httpx.HTTPStatusError):
            await admin_client.delete_user("missing")

    @pytest.mark.asyncio
    @respx.mock
    async def test_find_user_by_name_returns_match(self, admin_client, gns3_user):
        respx.get("http://gns3-server:3080/v3/access/users").mock(
            return_value=Response(
                200,
                json=[
                    gns3_user(user_id="u1", username="student-1"),
                    gns3_user(user_id="u2", username="student-2"),
                ],
            ),
        )
        result = await admin_client.find_user_by_name("student-2")
        assert result is not None
        assert result["user_id"] == "u2"

    @pytest.mark.asyncio
    @respx.mock
    async def test_find_user_by_name_returns_none_when_missing(self, admin_client, gns3_user):
        respx.get("http://gns3-server:3080/v3/access/users").mock(
            return_value=Response(200, json=[gns3_user(username="student-1")]),
        )
        result = await admin_client.find_user_by_name("ghost")
        assert result is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_user_token_returns_token(self, admin_client):
        respx.post("http://gns3-server:3080/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt-xyz"}),
        )
        token = await admin_client.get_user_token("student-1", "x")
        assert token == "jwt-xyz"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_user_token_raises_on_401(self, admin_client):
        respx.post("http://gns3-server:3080/v3/access/users/authenticate").mock(
            return_value=Response(401, json={"message": "bad creds"}),
        )
        with pytest.raises(httpx.HTTPStatusError):
            await admin_client.get_user_token("student-1", "wrong")
