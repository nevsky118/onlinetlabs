# WebSocket-эндпоинт стрима событий сессии.
#
# Эндпоинт публикуется только в docker-network gns3-service и потребляется
# backend-прокси. Дополнительная проверка shared secret через query-param
# `?token=...` защищает от случайного проброса порта наружу: если в конфиге
# задан INTERNAL_API_TOKEN, без валидного токена соединение закрывается.

import asyncio
import logging
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
    """Стрим событий сессии: snapshot на коннект, потом события из брокера.

    Heartbeat ping раз в 20 секунд для обхода idle-таймаутов прокси.
    """
    expected_token = getattr(settings.security, "internal_api_token", None)
    if expected_token:
        if not token or token != expected_token:
            # 1008 = Policy Violation по RFC 6455.
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

    ping_task = asyncio.create_task(send_pings())
    recv_task = asyncio.create_task(_recv_loop(websocket))
    subscription = broker.subscribe(session_id)
    try:
        async for event in subscription:
            if recv_task.done():
                break
            await websocket.send_json(event)
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    except Exception:
        logger.exception("ws_session_events error for %s", session_id)
    finally:
        ping_task.cancel()
        recv_task.cancel()
        try:
            await subscription.aclose()
        except Exception:
            pass


async def _recv_loop(websocket: WebSocket) -> None:
    """Дренировать входящие сообщения клиента до дисконнекта."""
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
    except Exception:
        return
