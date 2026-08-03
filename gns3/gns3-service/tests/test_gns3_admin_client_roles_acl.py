"""Unit tests for GNS3AdminClient RolesMixin and AclMixin."""

import httpx
import pytest
import respx
from httpx import Response
from mcp_sdk.testing import autotest

from src.clients.admin import GNS3AdminClient


class TestGns3AdminClientRoles:
    """Unit tests for role management through the HTTP wrapper."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3-server:3080", "admin", "pass")
        client.set_admin_token("fake")
        return client

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3309")
    @autotest.external_id("c538ca80-55c0-4dae-97e1-5288ef17a520")
    @autotest.name("GNS3AdminClient.get_builtin_role: returns the match and caches the result")
    async def test_c538ca80_get_builtin_role_returns_match_and_caches(self, admin_client):
        with autotest.step("Arrange: mock the roles endpoint with builtin and custom roles"):
            route = respx.get("http://gns3-server:3080/v3/access/roles").mock(
                return_value=Response(
                    200,
                    json=[
                        {"role_id": "r1", "name": "User", "is_builtin": True},
                        {"role_id": "r2", "name": "Administrator", "is_builtin": True},
                        {"role_id": "r3", "name": "Custom", "is_builtin": False},
                    ],
                ),
            )

        with autotest.step("Act: fetch the builtin role"):
            result = await admin_client.get_builtin_role("User")

        with autotest.step("Assert: the match is returned"):
            assert result["role_id"] == "r1"

        with autotest.step("Act: fetch the same role again"):
            # Repeat call, must be served from the cache without an HTTP request.
            result_cached = await admin_client.get_builtin_role("User")

        with autotest.step("Assert: still the match, served from cache without a new request"):
            assert result_cached["role_id"] == "r1"
            assert route.call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3310")
    @autotest.external_id("6ec6ac80-c15a-4d89-81c3-9d72e542e897")
    @autotest.name("GNS3AdminClient.get_builtin_role: raises when the role is missing")
    async def test_6ec6ac80_get_builtin_role_raises_when_missing(self, admin_client):
        with autotest.step("Arrange: mock the roles endpoint without the requested role"):
            respx.get("http://gns3-server:3080/v3/access/roles").mock(
                return_value=Response(
                    200,
                    json=[
                        {"role_id": "r1", "name": "User", "is_builtin": True},
                    ],
                ),
            )

        with autotest.step("Act + Assert: fetching a missing builtin role raises"):
            with pytest.raises(ValueError, match="Ghost"):
                await admin_client.get_builtin_role("Ghost")


class TestGns3AdminClientAcl:
    """Unit tests for ACL management through the HTTP wrapper."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3-server:3080", "admin", "pass")
        client.set_admin_token("fake")
        return client

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3311")
    @autotest.external_id("e09e93d3-2d74-49f1-80ed-97dc99958d69")
    @autotest.name("GNS3AdminClient.create_acl: returns the created ACE payload")
    async def test_e09e93d3_create_acl_returns_payload(self, admin_client):
        with autotest.step("Arrange: mock the ACL endpoint to return the created ace"):
            respx.post("http://gns3-server:3080/v3/access/acl").mock(
                return_value=Response(
                    201,
                    json={
                        "ace_id": "a1",
                        "path": "/projects/p1",
                        "role_id": "r1",
                        "user_id": "u1",
                        "ace_type": "user",
                        "allowed": True,
                    },
                ),
            )

        with autotest.step("Act: create the ACL"):
            result = await admin_client.create_acl(
                path="/projects/p1",
                role_id="r1",
                user_id="u1",
            )

        with autotest.step("Assert: the created ace is returned and allowed"):
            assert result["ace_id"] == "a1"
            assert result["allowed"] is True

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3312")
    @autotest.external_id("233ce7e0-d50b-4690-8da9-70f2076d4498")
    @autotest.name("GNS3AdminClient.create_acl: raises on 409 for a duplicate ACL")
    async def test_233ce7e0_create_acl_raises_on_409(self, admin_client):
        with autotest.step("Arrange: mock the ACL endpoint to return 409"):
            respx.post("http://gns3-server:3080/v3/access/acl").mock(
                return_value=Response(409, json={"message": "duplicate"}),
            )

        with autotest.step("Act + Assert: creating a duplicate ACL raises 409"):
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await admin_client.create_acl(
                    path="/projects/p1",
                    role_id="r1",
                    user_id="u1",
                )
            assert exc_info.value.response.status_code == 409
