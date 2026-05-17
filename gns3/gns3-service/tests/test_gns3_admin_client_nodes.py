"""Unit-тесты GNS3AdminClient.node_action / bulk_node_action."""

import pytest
import respx
from httpx import Response

from src.gns3_admin_client import GNS3AdminClient


class TestGns3AdminClientNodeAction:
    """Unit-тесты node_action и bulk_node_action."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3:3080", "u", "p")
        client._client.headers["Authorization"] = "Bearer fake"
        return client

    @pytest.mark.asyncio
    @respx.mock
    async def test_node_action_start_posts_to_expected_url(self, admin_client):
        respx.post("http://gns3:3080/v3/projects/p1/nodes/n1/start").mock(
            return_value=Response(200, json={"status": "started"}),
        )
        await admin_client.node_action("p1", "n1", "start")

    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_node_action_stop_posts_to_expected_url(self, admin_client):
        respx.post("http://gns3:3080/v3/projects/p1/nodes/stop").mock(
            return_value=Response(204),
        )
        await admin_client.bulk_node_action("p1", "stop")

    @pytest.mark.asyncio
    async def test_node_action_invalid_action_raises(self, admin_client):
        with pytest.raises(ValueError):
            await admin_client.node_action("p", "n", "delete")
