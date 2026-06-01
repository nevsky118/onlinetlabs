import pytest
import respx
from httpx import Response

from gns3_service_client import Gns3ServiceClient


@pytest.mark.asyncio
@respx.mock
async def test_get_state_returns_dict():
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
async def test_node_action_204_returns_none():
    sid, nid = "11111111-1111-1111-1111-111111111111", "n1"
    respx.post(f"http://gns3-svc:8101/sessions/{sid}/nodes/{nid}/start").mock(
        return_value=Response(204)
    )
    c = Gns3ServiceClient("http://gns3-svc:8101")
    assert (await c.node_action(sid, nid, "start")) is None
    await c.close()


@pytest.mark.asyncio
@respx.mock
async def test_bulk_node_action_204():
    sid = "11111111-1111-1111-1111-111111111111"
    respx.post(f"http://gns3-svc:8101/sessions/{sid}/nodes/stop").mock(
        return_value=Response(204)
    )
    c = Gns3ServiceClient("http://gns3-svc:8101")
    assert (await c.bulk_node_action(sid, "stop")) is None
    await c.close()


@pytest.mark.asyncio
@respx.mock
async def test_get_activity_returns_dict():
    sid = "11111111-1111-1111-1111-111111111111"
    respx.get(f"http://gns3-svc:8101/sessions/{sid}/activity").mock(
        return_value=Response(200, json={"events": [], "next_cursor": None})
    )
    c = Gns3ServiceClient("http://gns3-svc:8101")
    body = await c.get_activity(sid, limit=10)
    assert body["events"] == []
    assert body["next_cursor"] is None
    await c.close()
