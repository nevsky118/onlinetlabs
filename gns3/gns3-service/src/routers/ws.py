"""WebSocket endpoint for the session event stream, consumed by the backend proxy.

Port 8101 is published, so the shared secret is the actual guard: when
INTERNAL_API_TOKEN is configured, a connection without a matching `?token=` is
closed with 1008.
"""

import asyncio
import logging
import secrets
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/sessions/{session_id}/events")
async def ws_session_events(
    websocket: WebSocket,
    session_id: str,
    token: str | None = Query(default=None),
):
    """Session event stream: a snapshot on connect, then events from the broker.

    Heartbeat ping every 20 seconds to work around proxy idle timeouts.
    """
    expected_token = getattr(settings.security, "internal_api_token", None)
    if expected_token:
        if not token or not secrets.compare_digest(token, expected_token):
            # 1008 = Policy Violation per RFC 6455.
            await websocket.close(code=1008, reason="invalid token")
            return

    broker = websocket.app.state.event_broker
    ws_proxy = websocket.app.state.ws_proxy
    svc = websocket.app.state.session_service
    db_factory = websocket.app.state.db_factory

    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        await websocket.close(code=4404)
        return

    from src.db.models import Session

    async with db_factory() as db:
        session = await db.get(Session, session_uuid)
    if session is None:
        await websocket.close(code=4404)
        return

    await websocket.accept()

    try:
        await ws_proxy.start_project(session.gns3_project_id, session_id)
    except Exception:
        logger.exception("ws_proxy.start_project failed for %s", session_id)

    try:
        async with db_factory() as db:
            state = await svc.get_state(db=db, session_id=session_id)
        await websocket.send_json(
            {
                "type": "snapshot",
                "timestamp": datetime.now(UTC).isoformat(),
                "payload": state.model_dump(mode="json"),
            }
        )
    except Exception:
        logger.exception("snapshot failed for %s", session_id)

    async def send_pings():
        try:
            while True:
                await asyncio.sleep(20)
                await websocket.send_json(
                    {
                        "type": "ping",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "payload": {},
                    }
                )
        except Exception:
            return

    subscription = broker.subscribe(session_id)

    async def forward_events() -> None:
        async for event in subscription:
            await websocket.send_json(event)

    ping_task = asyncio.create_task(send_pings())
    recv_task = asyncio.create_task(_recv_loop(websocket))
    forward_task = asyncio.create_task(forward_events())
    tasks = {ping_task, recv_task, forward_task}
    try:
        # Race them. On an idle session the broker blocks in xread and never
        # yields, so a disconnect check inside the forward loop never runs and
        # the handler outlives the client. send_pings returning also means the
        # socket is gone.
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            try:
                task.result()
            except (WebSocketDisconnect, asyncio.CancelledError):
                pass
            except Exception:
                logger.exception("ws_session_events error for %s", session_id)
    finally:
        for task in tasks:
            task.cancel()
        try:
            await subscription.aclose()
        except Exception:
            pass


async def _recv_loop(websocket: WebSocket) -> None:
    """Drain incoming client messages until disconnect."""
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
    except Exception:
        return
