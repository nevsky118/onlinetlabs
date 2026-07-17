"""Unit-тесты GNS3AdminClient ProjectsMixin."""

import httpx
import pytest
import respx
from httpx import Response

from src.gns3_admin_client import GNS3AdminClient


class TestGns3AdminClientProjects:
    """Unit-тесты управления проектами через HTTP-обёртку."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3-server:3080", "admin", "pass")
        client.set_admin_token("fake")
        return client

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_project_returns_payload(self, admin_client, gns3_project):
        respx.post("http://gns3-server:3080/v3/projects").mock(
            return_value=Response(201, json=gns3_project(project_id="p1", name="lab-1")),
        )
        result = await admin_client.create_project(name="lab-1")
        assert result["project_id"] == "p1"
        assert result["name"] == "lab-1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_project_raises_on_409(self, admin_client):
        respx.post("http://gns3-server:3080/v3/projects").mock(
            return_value=Response(409, json={"message": "duplicate"}),
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await admin_client.create_project(name="lab-1")
        assert exc_info.value.response.status_code == 409

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_projects_returns_list(self, admin_client, gns3_project):
        respx.get("http://gns3-server:3080/v3/projects").mock(
            return_value=Response(
                200,
                json=[
                    gns3_project(project_id="p1", name="lab-1"),
                    gns3_project(project_id="p2", name="lab-2"),
                ],
            ),
        )
        result = await admin_client.list_projects()
        assert len(result) == 2
        assert result[0]["project_id"] == "p1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_projects_raises_on_500(self, admin_client):
        # _retry_on_401 не ретраит 500; transient_retry — только на сетевые/5xx
        # уровня httpx-ошибок, но он не применён к list_projects.
        respx.get("http://gns3-server:3080/v3/projects").mock(
            return_value=Response(500, json={"message": "boom"}),
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await admin_client.list_projects()
        assert exc_info.value.response.status_code == 500

    @pytest.mark.asyncio
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
