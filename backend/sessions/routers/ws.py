"""WebSocket-эндпоинты сессии: интервенции и поток событий из gns3-service."""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from auth.dependencies import decode_backend_token, verify_jwt_for_ws
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
async def session_interventions_ws(
    websocket: WebSocket, session_id: str, token: str = Query(...)
):
    """Поток интервенций (TutorAgent, HintAgent) для активной сессии."""
    try:
        payload = decode_backend_token(token, settings.api.jwt_secret)
        user_id = payload.get("sub")
    except Exception:
        await websocket.close(code=4401)
        return
    if not user_id:
        await websocket.close(code=4401)
        return

    gateway = websocket.app.state.gateway
    await gateway.connect(session_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        gateway.disconnect(session_id)


@router.websocket("/ws/{session_id}/events")
async def session_events_ws(
    websocket: WebSocket,
    session_id: str,
    token: str | None = Query(default=None),
):
    """Поток событий из gns3-service для клиента.

    Авторизация через ?token=<jwt>. Коды закрытия:
    4401 — токен отсутствует или невалиден,
    4404 — сессия не принадлежит пользователю,
    1011 — внутренняя ошибка форварда,
    1012 — остановка сервера (через close_all_connections).
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
            websocket, settings.gns3.service_url, gns3_sid,
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
