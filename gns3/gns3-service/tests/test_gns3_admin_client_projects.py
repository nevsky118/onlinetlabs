"""Unit tests for GNS3AdminClient ProjectsMixin."""

import httpx
import pytest
import respx
from httpx import Response

from src.clients.admin import GNS3AdminClient


class TestGns3AdminClientProjects:
    """Unit tests for project management through the HTTP wrapper."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3-server:3080", "admin", "pass")
        client.set_admin_token("fake")
        return client

    @respx.mock
    async def test_duplicate_project_returns_payload(self, admin_client, gns3_project):
        respx.post("http://gns3-server:3080/v3/projects/p1/duplicate").mock(
            return_value=Response(201, json=gns3_project(project_id="p1-copy", name="lab-1-copy")),
        )
        result = await admin_client.duplicate_project("p1", name="lab-1-copy")
        assert result["project_id"] == "p1-copy"

    @pytest.mark.asyncio
    @respx.mock
    async def test_duplicate_project_raises_on_404(self, admin_client):
        respx.post("http://gns3-server:3080/v3/projects/missing/duplicate").mock(
            return_value=Response(404, json={"message": "not found"}),
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await admin_client.duplicate_project("missing")
        assert exc_info.value.response.status_code == 404

    @pytest.mark.asyncio
    @respx.mock
    async def test_open_project_returns_payload(self, admin_client, gns3_project):
        respx.post("http://gns3-server:3080/v3/projects/p1/open").mock(
            return_value=Response(200, json=gns3_project(project_id="p1", status="opened")),
        )
        result = await admin_client.open_project("p1")
        assert result["project_id"] == "p1"
        assert result["status"] == "opened"

    @pytest.mark.asyncio
    @respx.mock
    async def test_open_project_raises_on_404(self, admin_client):
        respx.post("http://gns3-server:3080/v3/projects/missing/open").mock(
            return_value=Response(404, json={"message": "not found"}),
        )
        with pytest.raises(httpx.HTTPStatusError):
            await admin_client.open_project("missing")

    @pytest.mark.asyncio
    @respx.mock
    async def test_delete_project_ok(self, admin_client):
        route = respx.delete("http://gns3-server:3080/v3/projects/p1").mock(
            return_value=Response(204),
        )
        await admin_client.delete_project("p1")
        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_delete_project_raises_on_404(self, admin_client):
        respx.delete("http://gns3-server:3080/v3/projects/missing").mock(
            return_value=Response(404, json={"message": "not found"}),
        )
        with pytest.raises(httpx.HTTPStatusError):
            await admin_client.delete_project("missing")
