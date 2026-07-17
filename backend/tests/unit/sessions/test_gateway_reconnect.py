"""WebSocketGateway.disconnect: must not evict the new socket when the old one drops.

Regression: disconnect(session_id) removed the _connections entry keyed only by
session_id, without checking which socket was actually stored there. On reconnect
(page refresh), connect() overwrites _connections[session_id] with the new socket,
but the old socket can send a delayed WebSocketDisconnect AFTER the reconnect — its
disconnect(session_id) would evict the new (live) socket, and interventions would
silently stop reaching the student.
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
        "disconnect: отложенный disconnect старого сокета не вытесняет новый после reconnect"
    )
    async def test_501b5e1f_stale_disconnect_does_not_evict_new_socket(self):
        with autotest.step("Arrange: gateway, старый и новый сокет одной сессии"):
            gw = WebSocketGateway()
            ws_old, ws_new = _FakeWebSocket(), _FakeWebSocket()

        with autotest.step(
            "Act: connect(старый) → connect(новый, reconnect) → disconnect(старый) с опозданием"
        ):
            await gw.connect("s1", ws_old)
            await gw.connect("s1", ws_new)
            gw.disconnect("s1", ws_old)

        with autotest.step("Assert: новый сокет остался в _connections"):
            assert_true(
                gw._connections.get("s1") is ws_new, "новый сокет не вытеснен старым disconnect"
            )

    @autotest.num("2421")
    @autotest.external_id("175fcb15-48b5-4d74-8142-e1b512679a2f")
    @autotest.name("disconnect: тот же сокет, что подключён — удаляется из _connections")
    async def test_175fcb15_disconnect_same_socket_removes_connection(self):
        with autotest.step("Arrange: gateway с одним подключённым сокетом"):
            gw = WebSocketGateway()
            ws = _FakeWebSocket()
            await gw.connect("s1", ws)

        with autotest.step("Act: disconnect тем же сокетом"):
            gw.disconnect("s1", ws)

        with autotest.step("Assert: сессия удалена из _connections"):
            assert_true("s1" not in gw._connections, "сессия удалена")

    @autotest.num("2422")
    @autotest.external_id("5735fc50-e64a-4980-8898-b2ba7c9d2bab")
    @autotest.name(
        "disconnect: без websocket-аргумента сохраняет старое поведение (удаляет без проверки)"
    )
    async def test_5735fc50_disconnect_without_websocket_arg_removes_connection(self):
        with autotest.step("Arrange: gateway с одним подключённым сокетом"):
            gw = WebSocketGateway()
            ws = _FakeWebSocket()
            await gw.connect("s1", ws)

        with autotest.step("Act: disconnect без websocket (back-compat вызов)"):
            gw.disconnect("s1")

        with autotest.step("Assert: сессия удалена из _connections"):
            assert_true("s1" not in gw._connections, "сессия удалена")
