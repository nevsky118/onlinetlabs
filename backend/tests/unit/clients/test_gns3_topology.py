import pytest
import respx
from httpx import Response
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none

from clients.gns3 import Gns3ServiceClient

pytestmark = [pytest.mark.unit]


class TestGns3Topology:
    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3200")
    @autotest.external_id("5040dce9-b73c-4f3e-a0be-d6e413a3a1dc")
    @autotest.name("Gns3ServiceClient.get_state: returns session state as a dict")
    async def test_5040dce9_get_state_returns_dict(self):
        with autotest.step("Arrange: mock the session state endpoint and build the client"):
            sid = "11111111-1111-1111-1111-111111111111"
            respx.get(f"http://gns3-svc:8101/sessions/{sid}/state").mock(
                return_value=Response(
                    200,
                    json={
                        "session_id": sid,
                        "nodes": [],
                        "links": [],
                        "metrics": {},
                        "status": "active",
                    },
                )
            )
            client = Gns3ServiceClient("http://gns3-svc:8101")

        with autotest.step("Act: get_state"):
            state = await client.get_state(sid)

        with autotest.step("Assert: returned dict carries the session id"):
            assert_equal(state["session_id"], sid, "session id")
            await client.close()

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3201")
    @autotest.external_id("f504a542-6eaf-4f8c-bc2f-01273a792127")
    @autotest.name("Gns3ServiceClient.node_action: 204 response returns None")
    async def test_f504a542_node_action_204_returns_none(self):
        with autotest.step(
            "Arrange: mock the node start endpoint to return 204 and build the client"
        ):
            sid, nid = "11111111-1111-1111-1111-111111111111", "n1"
            respx.post(f"http://gns3-svc:8101/sessions/{sid}/nodes/{nid}/start").mock(
                return_value=Response(204)
            )
            client = Gns3ServiceClient("http://gns3-svc:8101")

        with autotest.step("Act+Assert: node_action returns None on 204"):
            assert_is_none(await client.node_action(sid, nid, "start"), "204 yields no body")
            await client.close()

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3202")
    @autotest.external_id("bb23eb2c-bf55-4784-b290-c012b25ddd9b")
    @autotest.name("Gns3ServiceClient.bulk_node_action: 204 response returns None")
    async def test_bb23eb2c_bulk_node_action_204(self):
        with autotest.step(
            "Arrange: mock the bulk stop endpoint to return 204 and build the client"
        ):
            sid = "11111111-1111-1111-1111-111111111111"
            respx.post(f"http://gns3-svc:8101/sessions/{sid}/nodes/stop").mock(
                return_value=Response(204)
            )
            client = Gns3ServiceClient("http://gns3-svc:8101")

        with autotest.step("Act+Assert: bulk_node_action returns None on 204"):
            assert_is_none(await client.bulk_node_action(sid, "stop"), "204 yields no body")
            await client.close()

    @pytest.mark.asyncio
    @respx.mock
    @autotest.num("3203")
    @autotest.external_id("56423012-f626-4261-ad90-ab984144a3fc")
    @autotest.name("Gns3ServiceClient.get_activity: returns activity events and next cursor")
    async def test_56423012_get_activity_returns_dict(self):
        with autotest.step("Arrange: mock the activity endpoint and build the client"):
            sid = "11111111-1111-1111-1111-111111111111"
            respx.get(f"http://gns3-svc:8101/sessions/{sid}/activity").mock(
                return_value=Response(200, json={"events": [], "next_cursor": None})
            )
            client = Gns3ServiceClient("http://gns3-svc:8101")

        with autotest.step("Act: get_activity"):
            body = await client.get_activity(sid, limit=10)

        with autotest.step("Assert: events list is empty and no next cursor"):
            assert_equal(body["events"], [], "events")
            assert_is_none(body["next_cursor"], "next cursor")
            await client.close()
