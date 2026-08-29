"""Unit tests for GNS3AdminClient.get_nodes / get_links."""

import pytest
import respx
from httpx import Response
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from src.clients.admin import GNS3AdminClient
from tests.settings.data.gns3_data import Gns3LinkData, Gns3NodeData

pytestmark = [pytest.mark.unit]


class TestGns3AdminClientTopology:
    """Unit tests for fetching the topology through the HTTP wrapper."""

    @pytest.fixture
    def admin_client(self):
        client = GNS3AdminClient("http://gns3-server:3080", "admin", "pass")
        client.set_admin_token("fake")
        return client

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3313")
    @autotest.external_id("cac56cf3-4f3b-4bf2-8a9d-ccad1b99c995")
    @autotest.name("GNS3AdminClient.get_nodes: returns the project's nodes with status")
    async def test_cac56cf3_get_nodes_returns_list(self, admin_client):
        with autotest.step("Arrange: mock the nodes endpoint with one node"):
            project_id = "11111111-1111-1111-1111-111111111111"
            respx.get(f"http://gns3-server:3080/v3/projects/{project_id}/nodes").mock(
                return_value=Response(
                    200,
                    json=[
                        Gns3NodeData(
                            node_id="n1",
                            name="R1",
                            node_type="dynamips",
                            status="started",
                            console=5000,
                            symbol=":/symbols/router.svg",
                        ).data,
                    ],
                ),
            )

        with autotest.step("Act: fetch the project's nodes"):
            result = await admin_client.get_nodes(project_id)

        with autotest.step("Assert: the node and its status are returned"):
            assert_equal(len(result), 1, "result count")
            assert_equal(result[0]["name"], "R1", "name")
            assert_equal(result[0]["status"], "started", "status")

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3314")
    @autotest.external_id("bb54248a-198f-4225-9fbf-f30d70d38bd2")
    @autotest.name("GNS3AdminClient.get_links: returns the project's links with endpoints")
    async def test_bb54248a_get_links_returns_list(self, admin_client):
        with autotest.step("Arrange: mock the links endpoint with one link"):
            project_id = "11111111-1111-1111-1111-111111111111"
            respx.get(f"http://gns3-server:3080/v3/projects/{project_id}/links").mock(
                return_value=Response(
                    200,
                    json=[
                        Gns3LinkData(
                            link_id="l1",
                            nodes=[
                                {"node_id": "n1", "adapter_number": 0, "port_number": 0},
                                {"node_id": "n2", "adapter_number": 0, "port_number": 0},
                            ],
                        ).data,
                    ],
                ),
            )

        with autotest.step("Act: fetch the project's links"):
            result = await admin_client.get_links(project_id)

        with autotest.step("Assert: the link and its endpoints are returned"):
            assert_equal(len(result), 1, "result count")
            assert_equal(result[0]["link_id"], "l1", "link id")
            assert_equal(len(result[0]["nodes"]), 2, "nodes count")
