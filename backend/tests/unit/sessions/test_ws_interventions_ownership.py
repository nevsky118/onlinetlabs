"""WS interventions endpoint: session_id must belong to the user.

Security regression: session_interventions_ws decoded the JWT but did not check
session ownership before gateway.connect. _connections in WebSocketGateway is a
single-slot dict[str, WebSocket], so connecting to someone else's session_id would
evict the real student's socket (session hijack / eviction), sending interventions to the wrong user.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocketDisconnect
from mcp_sdk.testing import autotest

from sessions.routers.ws import session_interventions_ws

pytestmark = [pytest.mark.unit]


class _FakeWebSocket:
    """Minimal WebSocket stub: close/accept/receive_text + app.state.gateway."""

    def __init__(self, gateway):
        self.close = AsyncMock()
        self.accept = AsyncMock()
        # By default receive_text immediately drops the connection, so an unfixed
        # handler (without an ownership check) doesn't hang in `while True` when called.
        self.receive_text = AsyncMock(side_effect=WebSocketDisconnect())
        self.app = SimpleNamespace(state=SimpleNamespace(gateway=gateway))


def _fake_gateway():
    gateway = MagicMock()
    gateway.connect = AsyncMock()
    gateway.disconnect = MagicMock()
    return gateway


class TestSessionInterventionsWsOwnership:
    @autotest.num("2410")
    @autotest.external_id("c205bb8c-ae3f-43d3-9d4b-b277f1d154ea")
    @autotest.name(
        "session_interventions_ws: чужая сессия, close(4404), gateway.connect не вызывается"
    )
    async def test_c205bb8c_rejects_session_not_owned_by_user(self):
        with autotest.step(
            "Arrange: валидный токен, get_session возвращает None (сессия не принадлежит user-1)"
        ):
            gateway = _fake_gateway()
            fake_ws = _FakeWebSocket(gateway)

        with autotest.step("Act: подключение к чужому session_id"):
            with (
                patch("sessions.routers.ws.decode_backend_token", return_value={"sub": "user-1"}),
                patch("sessions.routers.ws.get_session", new=AsyncMock(return_value=None)),
            ):
                await session_interventions_ws(fake_ws, "someone-elses-session", token="t")

        with autotest.step("Assert: закрыто с 4404, gateway.connect ни разу не вызван"):
            fake_ws.close.assert_awaited_once_with(code=4404)
            gateway.connect.assert_not_awaited()

    @autotest.num("2411")
    @autotest.external_id("9a0f526e-eedd-4701-9d72-0e996f5c8c95")
    @autotest.name(
        "session_interventions_ws: владелец сессии, gateway.connect вызывается, disconnect по обрыву"
    )
    async def test_9a0f526e_connects_owner_to_gateway(self):
        with autotest.step("Arrange: валидный токен, get_session возвращает сессию user-1"):
            gateway = _fake_gateway()
            fake_ws = _FakeWebSocket(gateway)
            owned_session = SimpleNamespace(id="session-1", user_id="user-1")

        with autotest.step("Act: подключение владельца к своей сессии"):
            with (
                patch("sessions.routers.ws.decode_backend_token", return_value={"sub": "user-1"}),
                patch("sessions.routers.ws.get_session", new=AsyncMock(return_value=owned_session)),
            ):
                await session_interventions_ws(fake_ws, "session-1", token="t")

        with autotest.step(
            "Assert: gateway.connect вызван с (session_id, websocket), disconnect при обрыве связи"
        ):
            gateway.connect.assert_awaited_once_with("session-1", fake_ws)
            gateway.disconnect.assert_called_once_with("session-1", fake_ws)
