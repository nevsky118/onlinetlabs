"""Unit tests for GNS3AdminClient ProjectsMixin."""

import httpx
import pytest
import respx
from httpx import Response
from mcp_sdk.testing import autotest

from src.clients.admin import GNS3AdminClient


class TestGns3AdminClientProjects:
    """Unit tests for project management through the HTTP wrapper."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3-server:3080", "admin", "pass")
        client.set_admin_token("fake")
        return client

    @respx.mock
    @autotest.num("3303")
    @autotest.external_id("e731eb6b-469a-42a3-97cc-936eab5433de")
    @autotest.name("GNS3AdminClient.duplicate_project: returns the duplicated project payload")
    async def test_e731eb6b_duplicate_project_returns_payload(self, admin_client, gns3_project):
        with autotest.step("Arrange: mock the duplicate endpoint to return the new project"):
            respx.post("http://gns3-server:3080/v3/projects/p1/duplicate").mock(
                return_value=Response(
                    201, json=gns3_project(project_id="p1-copy", name="lab-1-copy")
                ),
            )

        with autotest.step("Act: duplicate the project"):
            result = await admin_client.duplicate_project("p1", name="lab-1-copy")

        with autotest.step("Assert: the duplicated project id is returned"):
            assert result["project_id"] == "p1-copy"

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3304")
    @autotest.external_id("60441193-7ecd-4b88-8141-f109201d4875")
    @autotest.name("GNS3AdminClient.duplicate_project: raises on 404 for a missing project")
    async def test_60441193_duplicate_project_raises_on_404(self, admin_client):
        with autotest.step("Arrange: mock the duplicate endpoint to return 404"):
            respx.post("http://gns3-server:3080/v3/projects/missing/duplicate").mock(
                return_value=Response(404, json={"message": "not found"}),
            )

        with autotest.step("Act + Assert: duplicating a missing project raises 404"):
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await admin_client.duplicate_project("missing")
            assert exc_info.value.response.status_code == 404

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3305")
    @autotest.external_id("e14990d9-10c5-44b2-8559-c54559ea9cf6")
    @autotest.name("GNS3AdminClient.open_project: returns the opened project payload")
    async def test_e14990d9_open_project_returns_payload(self, admin_client, gns3_project):
        with autotest.step("Arrange: mock the open endpoint to return the opened project"):
            respx.post("http://gns3-server:3080/v3/projects/p1/open").mock(
                return_value=Response(200, json=gns3_project(project_id="p1", status="opened")),
            )

        with autotest.step("Act: open the project"):
            result = await admin_client.open_project("p1")

        with autotest.step("Assert: the project id and opened status are returned"):
            assert result["project_id"] == "p1"
            assert result["status"] == "opened"

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3306")
    @autotest.external_id("7fdae3ae-f7bd-49d0-8dc6-e6989964d9e4")
    @autotest.name("GNS3AdminClient.open_project: raises on 404 for a missing project")
    async def test_7fdae3ae_open_project_raises_on_404(self, admin_client):
        with autotest.step("Arrange: mock the open endpoint to return 404"):
            respx.post("http://gns3-server:3080/v3/projects/missing/open").mock(
                return_value=Response(404, json={"message": "not found"}),
            )

        with autotest.step("Act + Assert: opening a missing project raises"):
            with pytest.raises(httpx.HTTPStatusError):
                await admin_client.open_project("missing")

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3307")
    @autotest.external_id("e96db6f4-4c15-4ac0-89a8-98718102c94c")
    @autotest.name("GNS3AdminClient.delete_project: hits the delete route")
    async def test_e96db6f4_delete_project_ok(self, admin_client):
        with autotest.step("Arrange: mock the delete endpoint"):
            route = respx.delete("http://gns3-server:3080/v3/projects/p1").mock(
                return_value=Response(204),
            )

        with autotest.step("Act: delete the project"):
            await admin_client.delete_project("p1")

        with autotest.step("Assert: the delete route was hit"):
            assert route.called

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3308")
    @autotest.external_id("f3409f37-cb48-4e31-ab00-aa7828fbd726")
    @autotest.name("GNS3AdminClient.delete_project: raises on 404 for a missing project")
    async def test_f3409f37_delete_project_raises_on_404(self, admin_client):
        with autotest.step("Arrange: mock the delete endpoint to return 404"):
            respx.delete("http://gns3-server:3080/v3/projects/missing").mock(
                return_value=Response(404, json={"message": "not found"}),
            )

        with autotest.step("Act + Assert: deleting a missing project raises"):
            with pytest.raises(httpx.HTTPStatusError):
                await admin_client.delete_project("missing")
