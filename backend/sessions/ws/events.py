"""Прокидывает WS-события из gns3-service клиенту.

На каждое клиентское соединение:
1. Открываем upstream WS к gns3-service /sessions/{sid}/events.
2. Гоняем сообщения в обе стороны.
3. При закрытии одной стороны корректно закрываем другую.
"""

from __future__ import annotations

import asyncio
import logging

import websockets
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


async def forward_session_events(
    client_ws: WebSocket,
    gns3_service_url: str,
    gns3_service_session_id: str,
) -> None:
    """Открывает upstream WS к gns3-service и гоняет события в обе стороны до закрытия."""
    # Подключаемся к gns3-service WS с internal-token, иначе сервер закроет соединение кодом 1008.
    from config import settings

    upstream_url = (
        gns3_service_url.replace("http://", "ws://").replace("https://", "wss://")
        + f"/sessions/{gns3_service_session_id}/events"
        + f"?token={settings.security.internal_api_token}"
    )

    async with websockets.connect(upstream_url) as upstream:

        async def upstream_to_client() -> None:
            """Пересылает сообщения от gns3-service клиентскому сокету."""
            try:
                async for raw in upstream:
                    text = raw if isinstance(raw, str) else raw.decode("utf-8", errors="ignore")
                    await client_ws.send_text(text)
            except Exception as exc:
                logger.debug("upstream_to_client closed: %s", exc)

        async def client_to_upstream() -> None:
            """Пересылает сообщения от клиента сокету gns3-service."""
            try:
                while True:
                    msg = await client_ws.receive_text()
                    await upstream.send(msg)
            except WebSocketDisconnect:
                pass
            except Exception as exc:
                logger.debug("client_to_upstream closed: %s", exc)

        u2c = asyncio.create_task(upstream_to_client())
        c2u = asyncio.create_task(client_to_upstream())
        done, pending = await asyncio.wait(
            [u2c, c2u],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        for task in pending:
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
