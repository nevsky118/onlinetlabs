import pytest
import respx
from httpx import Response
from mcp_sdk.testing import autotest

from gns3_service_client import Gns3ServiceClient


@pytest.mark.asyncio
@respx.mock
@autotest.num("3200")
@autotest.external_id("5040dce9-b73c-4f3e-a0be-d6e413a3a1dc")
@autotest.name("Gns3ServiceClient.get_state: returns session state as a dict")
async def test_5040dce9_get_state_returns_dict():
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
    c = Gns3ServiceClient("http://gns3-svc:8101")
    state = await c.get_state(sid)
    assert state["session_id"] == sid
    await c.close()


@pytest.mark.asyncio
@respx.mock
@autotest.num("3201")
@autotest.external_id("f504a542-6eaf-4f8c-bc2f-01273a792127")
@autotest.name("Gns3ServiceClient.node_action: 204 response returns None")
async def test_f504a542_node_action_204_returns_none():
    sid, nid = "11111111-1111-1111-1111-111111111111", "n1"
    respx.post(f"http://gns3-svc:8101/sessions/{sid}/nodes/{nid}/start").mock(
        return_value=Response(204)
    )
    c = Gns3ServiceClient("http://gns3-svc:8101")
    assert (await c.node_action(sid, nid, "start")) is None
    await c.close()


@pytest.mark.asyncio
@respx.mock
@autotest.num("3202")
@autotest.external_id("bb23eb2c-bf55-4784-b290-c012b25ddd9b")
@autotest.name("Gns3ServiceClient.bulk_node_action: 204 response returns None")
async def test_bb23eb2c_bulk_node_action_204():
    sid = "11111111-1111-1111-1111-111111111111"
    respx.post(f"http://gns3-svc:8101/sessions/{sid}/nodes/stop").mock(return_value=Response(204))
    c = Gns3ServiceClient("http://gns3-svc:8101")
    assert (await c.bulk_node_action(sid, "stop")) is None
    await c.close()


@pytest.mark.asyncio
@respx.mock
@autotest.num("3203")
@autotest.external_id("56423012-f626-4261-ad90-ab984144a3fc")
@autotest.name("Gns3ServiceClient.get_activity: returns activity events and next cursor")
async def test_56423012_get_activity_returns_dict():
    sid = "11111111-1111-1111-1111-111111111111"
    respx.get(f"http://gns3-svc:8101/sessions/{sid}/activity").mock(
        return_value=Response(200, json={"events": [], "next_cursor": None})
    )
    c = Gns3ServiceClient("http://gns3-svc:8101")
    body = await c.get_activity(sid, limit=10)
    assert body["events"] == []
    assert body["next_cursor"] is None
    await c.close()
