"""WebSocketGateway.disconnect: не должен вытеснять новый сокет по обрыву старого.

Регрессия: disconnect(session_id) удалял запись из _connections по одному только
session_id, без проверки, какой именно сокет там лежит. На reconnect (page refresh)
connect() перезаписывает _connections[session_id] новым сокетом, но старый сокет
может прислать отложенный WebSocketDisconnect уже ПОСЛЕ переподключения — его
disconnect(session_id) выбивал новый (живой) сокет, и интервенции студенту молча
переставали доходить.
"""

from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_true

from sessions.ws.gateway import WebSocketGateway

pytestmark = [pytest.mark.unit]


class _FakeWebSocket:
    """Минимальный WebSocket-стаб: gateway.connect нужен только async accept()."""

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
