"""Unit tests for GNS3AdminClient UsersMixin."""

import httpx
import pytest
import respx
from httpx import Response
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_is_none,
    assert_is_not_none,
    assert_true,
)

from src.clients.admin import GNS3AdminClient
from tests.settings.data.gns3_data import Gns3UserData

pytestmark = [pytest.mark.unit]


class TestGns3AdminClientUsers:
    """Unit tests for user management through the HTTP wrapper."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3-server:3080", "admin", "pass")
        client.set_admin_token("fake")
        return client

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3315")
    @autotest.external_id("02a44278-a66a-439c-8a56-7de13dc686ab")
    @autotest.name("GNS3AdminClient.create_user: returns the created user payload")
    async def test_02a44278_create_user_returns_payload(self, admin_client):
        with autotest.step("Arrange: mock the users endpoint to return the created user"):
            respx.post("http://gns3-server:3080/v3/access/users").mock(
                return_value=Response(
                    201, json=Gns3UserData(user_id="u1", username="student-1").data
                ),
            )

        with autotest.step("Act: create the user"):
            result = await admin_client.create_user(username="student-1", password="x")

        with autotest.step("Assert: the created user id and username are returned"):
            assert_equal(result["user_id"], "u1", "user id")
            assert_equal(result["username"], "student-1", "username")

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3316")
    @autotest.external_id("3fafd6eb-bd7f-408f-acd2-fc58fa4603c3")
    @autotest.name("GNS3AdminClient.create_user: raises on 409 for a duplicate user")
    async def test_3fafd6eb_create_user_raises_on_409(self, admin_client):
        with autotest.step("Arrange: mock the users endpoint to return 409"):
            respx.post("http://gns3-server:3080/v3/access/users").mock(
                return_value=Response(409, json={"message": "already registered"}),
            )

        with autotest.step("Act + Assert: creating a duplicate user raises 409"):
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await admin_client.create_user(username="student-1", password="x")
            assert_equal(exc_info.value.response.status_code, 409, "status code")

    @respx.mock
    @autotest.num("3317")
    @autotest.external_id("6a110a53-b7b0-49da-abda-934ae7a8cd36")
    @autotest.name("GNS3AdminClient.delete_user: hits the delete route")
    async def test_6a110a53_delete_user_ok(self, admin_client):
        with autotest.step("Arrange: mock the delete user endpoint"):
            route = respx.delete("http://gns3-server:3080/v3/access/users/u1").mock(
                return_value=Response(204),
            )

        with autotest.step("Act: delete the user"):
            await admin_client.delete_user("u1")

        with autotest.step("Assert: the delete route was hit"):
            assert_true(route.called, "called")

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3318")
    @autotest.external_id("ab2e7da7-46cd-4c10-ab4f-42cf757e1c57")
    @autotest.name("GNS3AdminClient.delete_user: raises on 404 for a missing user")
    async def test_ab2e7da7_delete_user_raises_on_404(self, admin_client):
        with autotest.step("Arrange: mock the delete user endpoint to return 404"):
            respx.delete("http://gns3-server:3080/v3/access/users/missing").mock(
                return_value=Response(404, json={"message": "not found"}),
            )

        with autotest.step("Act + Assert: deleting a missing user raises"):
            with pytest.raises(httpx.HTTPStatusError):
                await admin_client.delete_user("missing")

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3319")
    @autotest.external_id("3f9d84f9-0603-4aa4-a3eb-578602f090f5")
    @autotest.name("GNS3AdminClient.find_user_by_name: returns the matching user")
    async def test_3f9d84f9_find_user_by_name_returns_match(self, admin_client):
        with autotest.step("Arrange: mock the users endpoint with two users"):
            respx.get("http://gns3-server:3080/v3/access/users").mock(
                return_value=Response(
                    200,
                    json=[
                        Gns3UserData(user_id="u1", username="student-1").data,
                        Gns3UserData(user_id="u2", username="student-2").data,
                    ],
                ),
            )

        with autotest.step("Act: find a user by name"):
            result = await admin_client.find_user_by_name("student-2")

        with autotest.step("Assert: the matching user is returned"):
            assert_is_not_none(result, "result")
            assert_equal(result["user_id"], "u2", "user id")

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3320")
    @autotest.external_id("7fc89d41-4aa2-4dbb-bd15-8b72896595ee")
    @autotest.name("GNS3AdminClient.find_user_by_name: returns None when no match exists")
    async def test_7fc89d41_find_user_by_name_returns_none_when_missing(self, admin_client):
        with autotest.step("Arrange: mock the users endpoint without the searched name"):
            respx.get("http://gns3-server:3080/v3/access/users").mock(
                return_value=Response(200, json=[Gns3UserData(username="student-1").data]),
            )

        with autotest.step("Act: find a user by a name that does not exist"):
            result = await admin_client.find_user_by_name("ghost")

        with autotest.step("Assert: no match is returned"):
            assert_is_none(result, "result")

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3321")
    @autotest.external_id("170c1c57-6073-4919-8f28-b65f29e1e64b")
    @autotest.name("GNS3AdminClient.get_user_token: returns the access token")
    async def test_170c1c57_get_user_token_returns_token(self, admin_client):
        with autotest.step("Arrange: mock the authenticate endpoint to return a token"):
            respx.post("http://gns3-server:3080/v3/access/users/authenticate").mock(
                return_value=Response(200, json={"access_token": "jwt-xyz"}),
            )

        with autotest.step("Act: authenticate the user"):
            token = await admin_client.get_user_token("student-1", "x")

        with autotest.step("Assert: the access token is returned"):
            assert_equal(token, "jwt-xyz", "token")

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3322")
    @autotest.external_id("6ffddf1f-6f39-45d6-8757-59dd50799236")
    @autotest.name("GNS3AdminClient.get_user_token: raises on 401 for wrong credentials")
    async def test_6ffddf1f_get_user_token_raises_on_401(self, admin_client):
        with autotest.step("Arrange: mock the authenticate endpoint to return 401"):
            respx.post("http://gns3-server:3080/v3/access/users/authenticate").mock(
                return_value=Response(401, json={"message": "bad creds"}),
            )

        with autotest.step("Act + Assert: authenticating with wrong credentials raises"):
            with pytest.raises(httpx.HTTPStatusError):
                await admin_client.get_user_token("student-1", "wrong")
