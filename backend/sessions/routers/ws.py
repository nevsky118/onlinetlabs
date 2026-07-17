"""Session WebSocket endpoints: interventions and the gns3-service event stream."""

import asyncio
import contextlib
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from auth.dependencies import can_view_session_activity, decode_backend_token, verify_jwt_for_ws
from config import settings
from db.session import async_session
from sessions.service import get_session
from sessions.ws import (
    forward_session_events,
    register_connection,
    unregister_connection,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/sessions/{session_id}")
async def session_interventions_ws(websocket: WebSocket, session_id: str, token: str = Query(...)):
    """Intervention stream (TutorAgent, HintAgent) for an active session."""
    try:
        payload = decode_backend_token(token, settings.api.jwt_secret)
        user_id = payload.get("sub")
    except Exception:
        await websocket.close(code=4401)
        return
    if not user_id:
        await websocket.close(code=4401)
        return

    async with async_session() as db:
        session = await get_session(db, session_id, user_id)
    if session is None:
        await websocket.close(code=4404)
        return

    gateway = websocket.app.state.gateway
    await gateway.connect(session_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        gateway.disconnect(session_id, websocket)


@router.websocket("/ws/{session_id}/events")
async def session_events_ws(
    websocket: WebSocket,
    session_id: str,
    token: str | None = Query(default=None),
):
    """Event stream from gns3-service for the client.

    Authorization via ?token=<jwt>. Close codes:
    4401 — token missing or invalid,
    4404 — session doesn't belong to the user,
    1011 — internal forwarding error,
    1012 — server shutdown (via close_all_connections).
    """
    user = await verify_jwt_for_ws(token)
    if user is None:
        await websocket.close(code=4401)
        return

    async with async_session() as db:
        session = await get_session(db, session_id, user["id"])
    if session is None:
        await websocket.close(code=4404)
        return

    gns3_sid = (session.meta or {}).get("gns3_service_session_id")
    if not gns3_sid:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    register_connection(websocket)
    try:
        await forward_session_events(
            websocket,
            settings.gns3.service_url,
            gns3_sid,
        )
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WS forward error for session %s", session_id)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        unregister_connection(websocket)


@router.websocket("/ws/observe/{session_id}")
async def session_activity_observe_ws(
    websocket: WebSocket, session_id: str, token: str = Query(...)
):
    """Agent activity stream for an observer (instructor/admin)."""
    user = await verify_jwt_for_ws(token)
    if user is None:
        await websocket.close(code=4401)
        return
    async with async_session() as db:
        from models.session import LearningSession

        session = await db.get(LearningSession, session_id)
    if session is None or not can_view_session_activity(user, session):
        await websocket.close(code=4403)
        return
    activity = websocket.app.state.activity_log
    gateway = websocket.app.state.gateway
    await websocket.accept()
    gateway.connect_observer(session_id, websocket)
    q = activity.subscribe(session_id)
    try:

        async def _pump() -> None:
            while True:
                event = await q.get()
                await websocket.send_json(
                    {"type": "agent_activity", **event.model_dump(mode="json")}
                )

        async def _watch_disconnect() -> None:
            # receive() raises WebSocketDisconnect when the client disconnects,
            # even while _pump is blocked on an empty queue — otherwise the
            # handler would hang forever, leaking a task and a subscription.
            while True:
                await websocket.receive()

        pump = asyncio.create_task(_pump())
        watch = asyncio.create_task(_watch_disconnect())
        done, pending = await asyncio.wait({pump, watch}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        for task in done:
            with contextlib.suppress(WebSocketDisconnect, asyncio.CancelledError):
                task.result()
    finally:
        activity.unsubscribe(session_id, q)
        gateway.disconnect_observer(session_id, websocket)
