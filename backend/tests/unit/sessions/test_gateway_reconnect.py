"""Test: a stale disconnect must not evict the socket that replaced it.

Regression: disconnect keyed only on session_id, so a delayed WebSocketDisconnect
from a refreshed page removed the live socket and interventions stopped arriving.
A session now holds a set, and a disconnect removes only the socket it names.
"""

from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_true

from sessions.ws.gateway import WebSocketGateway

pytestmark = [pytest.mark.unit]


class _FakeWebSocket:
    """Minimal WebSocket stub: gateway.connect only needs async accept()."""

    def __init__(self):
        self.accept = AsyncMock()


class TestGatewayReconnect:
    @autotest.num("2420")
    @autotest.external_id("501b5e1f-2e42-4094-ab5a-84fa33cd4439")
    @autotest.name(
        "disconnect: a stale disconnect of the old socket does not evict the new one after reconnect"
    )
    async def test_501b5e1f_stale_disconnect_does_not_evict_new_socket(self):
        with autotest.step("Arrange: gateway, old and new socket of the same session"):
            gw = WebSocketGateway()
            ws_old, ws_new = _FakeWebSocket(), _FakeWebSocket()

        with autotest.step(
            "Act: connect(old) → connect(new, reconnect) → disconnect(old) with delay"
        ):
            await gw.connect("s1", ws_old)
            await gw.connect("s1", ws_new)
            gw.disconnect("s1", ws_old)

        with autotest.step("Assert: new socket remains in _connections"):
            assert_true(
                gw._connections.get("s1") == {ws_new}, "new socket survives the stale disconnect"
            )

    @autotest.num("2421")
    @autotest.external_id("175fcb15-48b5-4d74-8142-e1b512679a2f")
    @autotest.name("disconnect: the same socket that connected is removed from _connections")
    async def test_175fcb15_disconnect_same_socket_removes_connection(self):
        with autotest.step("Arrange: gateway with one connected socket"):
            gw = WebSocketGateway()
            ws = _FakeWebSocket()
            await gw.connect("s1", ws)

        with autotest.step("Act: disconnect with the same socket"):
            gw.disconnect("s1", ws)

        with autotest.step("Assert: session removed from _connections"):
            assert_true("s1" not in gw._connections, "session removed")

    @autotest.num("2422")
    @autotest.external_id("5735fc50-e64a-4980-8898-b2ba7c9d2bab")
    @autotest.name(
        "disconnect: without a websocket argument keeps old behavior (removes without checking)"
    )
    async def test_5735fc50_disconnect_without_websocket_arg_removes_connection(self):
        with autotest.step("Arrange: gateway with one connected socket"):
            gw = WebSocketGateway()
            ws = _FakeWebSocket()
            await gw.connect("s1", ws)

        with autotest.step("Act: disconnect without websocket (back-compat call)"):
            gw.disconnect("s1")

        with autotest.step("Assert: session removed from _connections"):
            assert_true("s1" not in gw._connections, "session removed")
