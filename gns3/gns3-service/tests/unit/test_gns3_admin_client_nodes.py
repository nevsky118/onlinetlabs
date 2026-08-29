"""Unit tests for GNS3AdminClient.node_action / bulk_node_action."""

import pytest
import respx
from httpx import Response
from mcp_sdk.testing import autotest

from src.clients.admin import GNS3AdminClient

pytestmark = [pytest.mark.unit]


class TestGns3AdminClientNodeAction:
    """Unit tests for node_action and bulk_node_action."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3:3080", "u", "p")
        client._client.headers["Authorization"] = "Bearer fake"
        return client

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3300")
    @autotest.external_id("f8ade05b-b957-4732-8cba-f6c6c441d021")
    @autotest.name("GNS3AdminClient.node_action: posts to the expected start URL")
    async def test_f8ade05b_node_action_start_posts_to_expected_url(self, admin_client):
        with autotest.step("Arrange: mock the node start endpoint"):
            respx.post("http://gns3:3080/v3/projects/p1/nodes/n1/start").mock(
                return_value=Response(200, json={"status": "started"}),
            )

        with autotest.step("Act: request the start action on a node"):
            await admin_client.node_action("p1", "n1", "start")

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3301")
    @autotest.external_id("58ae0f6a-19ca-4b9b-a255-e3b005f16e9d")
    @autotest.name("GNS3AdminClient.bulk_node_action: posts to the expected stop URL")
    async def test_58ae0f6a_bulk_node_action_stop_posts_to_expected_url(self, admin_client):
        with autotest.step("Arrange: mock the bulk node stop endpoint"):
            respx.post("http://gns3:3080/v3/projects/p1/nodes/stop").mock(
                return_value=Response(204),
            )

        with autotest.step("Act: request the stop action on all nodes"):
            await admin_client.bulk_node_action("p1", "stop")

    @pytest.mark.asyncio
    @autotest.num("3302")
    @autotest.external_id("f91ceeb5-1e66-4687-bd6d-7ac281857ab3")
    @autotest.name("GNS3AdminClient.node_action: an unknown action raises ValueError")
    async def test_f91ceeb5_node_action_invalid_action_raises(self, admin_client):
        with autotest.step("Act + Assert: an unknown action raises ValueError"):
            with pytest.raises(ValueError):
                await admin_client.node_action("p", "n", "delete")
