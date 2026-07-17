"""WS observer endpoint (/ws/observe/{session_id}): permission check + event forwarding.

Verifies can_view_session_activity (closes 4403 without the can_view_logs right) and
that a real AgentActivityLog.emit reaches the subscribed observer as
{"type": "agent_activity", ...}. Goes through the real ASGI stack (httpx-ws +
ASGIWebSocketTransport) rather than a direct handler call, the same way a
browser would (JWT in query, real accept/close).

The handler (sessions/routers/ws.py:session_activity_observe_ws) races _pump
(activity queue) against _watch_disconnect (websocket.receive), so a client
disconnect is noticed even with an empty queue and the subscription is removed
(see the disconnect_cleans_up_subscription test). asyncio.timeout in the tests is
a safeguard against a regression of this leak, not the expected path.
"""

import asyncio

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from httpx_ws import WebSocketDisconnect, aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from auth.dependencies import create_backend_token
from models.agent_activity_event import AgentActivityEventRow
from models.session import LearningSession
from observability.activity import AgentActivityLog
from observability.models import ActivityKind, ActivitySource, AgentActivityEvent
from sessions.routers.ws import router as ws_router
from sessions.ws.gateway import WebSocketGateway

pytestmark = [pytest.mark.unit]

_OWNER_ID = "user-obs-owner"
_SESSION_ID = "sess-obs-1"


class TestSessionActivityObserveWs:
    @pytest.fixture(autouse=True)
    async def setup(self, monkeypatch, sqlite_session_factory):
        session_factory = await sqlite_session_factory(
            [LearningSession.__table__, AgentActivityEventRow.__table__]
        )
        async with session_factory() as db:
            db.add(
                LearningSession(
                    id=_SESSION_ID,
                    user_id=_OWNER_ID,
                    lab_slug="lab-obs",
                    status="active",
                )
            )
            await db.commit()

        monkeypatch.setattr("sessions.routers.ws.async_session", session_factory)

        app = FastAPI()
        app.include_router(ws_router)
        app.state.gateway = WebSocketGateway()
        app.state.activity_log = AgentActivityLog(
            db_factory=session_factory, retention_per_session=100
        )
        self.app = app

    def _token(self, *, can_view_logs: bool) -> str:
        return create_backend_token(_OWNER_ID, role="student", can_view_logs=can_view_logs)

    @autotest.num("2650")
    @autotest.external_id("420ec7d3-0fe6-4b34-a81d-f643f363e211")
    @autotest.name(
        "session_activity_observe_ws: без can_view_logs, close(4403), can_view_session_activity"
    )
    async def test_420ec7d3_rejects_user_without_view_permission(self):
        with autotest.step("Arrange: валидный JWT владельца сессии, но без права can_view_logs"):
            token = self._token(can_view_logs=False)
            transport = ASGIWebSocketTransport(app=self.app)

        with autotest.step("Act: подключение к /ws/observe/{session_id}"):
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                with pytest.raises(WebSocketDisconnect) as exc_info:
                    async with aconnect_ws(f"/ws/observe/{_SESSION_ID}?token={token}", client):
                        pytest.fail("соединение не должно быть принято")

        with autotest.step("Assert: закрыто с кодом 4403 (can_view_session_activity=False)"):
            assert_equal(exc_info.value.code, 4403, "close code 4403")

    @autotest.num("2651")
    @autotest.external_id("b59676e3-71ef-49db-a61f-d2a29a373888")
    @autotest.name(
        "session_activity_observe_ws: авторизованный наблюдатель получает activity-событие"
    )
    async def test_b59676e3_forwards_activity_event_to_authorized_viewer(self):
        with autotest.step("Arrange: JWT владельца сессии с правом can_view_logs"):
            token = self._token(can_view_logs=True)
            transport = ASGIWebSocketTransport(app=self.app)

        with autotest.step(
            "Act: подключение, дождаться subscribe() внутри хендлера, эмитить событие"
        ):
            received = None
            try:
                async with asyncio.timeout(2):
                    async with AsyncClient(
                        transport=transport, base_url="http://testserver"
                    ) as client:
                        async with aconnect_ws(
                            f"/ws/observe/{_SESSION_ID}?token={token}", client
                        ) as ws:
                            for _ in range(500):
                                if _SESSION_ID in self.app.state.activity_log._subs:
                                    break
                                await asyncio.sleep(0)
                            else:
                                pytest.fail("хендлер не подписался на activity log вовремя")

                            event = AgentActivityEvent(
                                session_id=_SESSION_ID,
                                user_id=_OWNER_ID,
                                source=ActivitySource.INTERVENTION,
                                kind=ActivityKind.HINT_GENERATED,
                                summary="test hint",
                            )
                            self.app.state.activity_log.emit(event)
                            received = await ws.receive_json()
            except TimeoutError:
                # Expected way to break out of a hung server task (see the module
                # docstring), the assert below would already have run by this point.
                pass

        with autotest.step("Assert: событие форвардится как agent_activity с полями исходного"):
            assert received is not None, "событие должно быть получено до таймаута"
            assert_equal(received["type"], "agent_activity", "type=agent_activity")
            assert_equal(received["session_id"], _SESSION_ID, "session_id форвардится")
            assert_equal(received["summary"], "test hint", "summary форвардится")

    @autotest.num("2652")
    @autotest.external_id("e3d9c3a0-6557-4c68-85a8-7d89d6926def")
    @autotest.name(
        "session_activity_observe_ws: отключение клиента снимает подписку (нет утечки задачи)"
    )
    async def test_e3d9c3a0_disconnect_cleans_up_subscription(self):
        activity = self.app.state.activity_log
        token = self._token(can_view_logs=True)
        transport = ASGIWebSocketTransport(app=self.app)

        with autotest.step("Act: наблюдатель подключается, дожидается подписки, затем отключается"):
            # asyncio.timeout is a safeguard: before the fix, the handler would hang on
            # q.get() and unsubscribe would never be called, so the test would time out.
            async with asyncio.timeout(5):
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    async with aconnect_ws(f"/ws/observe/{_SESSION_ID}?token={token}", client):
                        for _ in range(500):
                            if _SESSION_ID in activity._subs:
                                break
                            await asyncio.sleep(0)
                        else:
                            pytest.fail("хендлер не подписался вовремя")
                    # exited aconnect_ws → client disconnected; the handler should
                    # notice the disconnect and remove the subscription.
                    for _ in range(500):
                        if _SESSION_ID not in activity._subs:
                            break
                        await asyncio.sleep(0)

        with autotest.step("Assert: подписка снята после disconnect (хендлер не завис)"):
            assert _SESSION_ID not in activity._subs, "подписка должна быть снята после disconnect"
