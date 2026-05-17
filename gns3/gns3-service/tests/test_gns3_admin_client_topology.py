"""Unit-тесты GNS3AdminClient.get_nodes / get_links."""

import pytest
import respx
from httpx import Response

from src.gns3_admin_client import GNS3AdminClient


class TestGns3AdminClientTopology:
    """Unit-тесты получения топологии через HTTP-обёртку."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3-server:3080", "admin", "pass")
        client.set_admin_token("fake")
        return client

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_nodes_returns_list(self, admin_client, gns3_node):
        project_id = "11111111-1111-1111-1111-111111111111"
        respx.get(f"http://gns3-server:3080/v3/projects/{project_id}/nodes").mock(
            return_value=Response(200, json=[
                gns3_node(node_id="n1", name="R1", node_type="dynamips", status="started",
                          console=5000, symbol=":/symbols/router.svg"),
            ]),
        )
        result = await admin_client.get_nodes(project_id)
        assert len(result) == 1
        assert result[0]["name"] == "R1"
        assert result[0]["status"] == "started"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_links_returns_list(self, admin_client, gns3_link):
        project_id = "11111111-1111-1111-1111-111111111111"
        respx.get(f"http://gns3-server:3080/v3/projects/{project_id}/links").mock(
            return_value=Response(200, json=[
                gns3_link(link_id="l1", nodes=[
                    {"node_id": "n1", "adapter_number": 0, "port_number": 0},
                    {"node_id": "n2", "adapter_number": 0, "port_number": 0},
                ]),
            ]),
        )
        result = await admin_client.get_links(project_id)
        assert len(result) == 1
        assert result[0]["link_id"] == "l1"
        assert len(result[0]["nodes"]) == 2
