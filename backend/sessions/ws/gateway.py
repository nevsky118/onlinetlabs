"""WebSocket gateway — управление соединениями и доставка интервенций.

Объединяет per-session connections для интервенций и глобальный реестр всех
активных сокетов для graceful shutdown (forward gns3 events + интервенции).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import WebSocket

logger = logging.getLogger(__name__)

_active_connections: set[WebSocket] = set()


def register_connection(ws: WebSocket) -> None:
    """Добавляет сокет в глобальный реестр активных соединений."""
    _active_connections.add(ws)


def unregister_connection(ws: WebSocket) -> None:
    """Убирает сокет из глобального реестра активных соединений."""
    _active_connections.discard(ws)


async def close_all_connections(timeout: float = 5.0) -> None:
    """Закрыть все активные клиентские WS с кодом 1012 (service restart)."""
    for ws in list(_active_connections):
        try:
            await ws.close(code=1012)
        except Exception:
            pass
    await asyncio.sleep(min(0.5, timeout))
    _active_connections.clear()


class WebSocketGateway:
    """Управление WebSocket-соединениями по session_id для интервенций."""

    def __init__(self):
        """Хранит словарь активных WebSocket-соединений по идентификатору сессии."""
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Зарегистрировать WebSocket для сессии."""
        await websocket.accept()
        self._connections[session_id] = websocket
        register_connection(websocket)

    def disconnect(self, session_id: str) -> None:
        """Удалить WebSocket сессии."""
        ws = self._connections.pop(session_id, None)
        if ws is not None:
            unregister_connection(ws)

    async def send_intervention(self, session_id: str, intervention_data: dict) -> None:
        """Отправить интервенцию студенту через WebSocket."""
        websocket = self._connections.get(session_id)
        if not websocket:
            logger.warning("WebSocket не найден для сессии %s", session_id)
            return

        payload = {
            "type": "intervention",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            **intervention_data,
        }
        try:
            await websocket.send_json(payload)
        except Exception:
            logger.warning(
                "Не удалось отправить интервенцию в сессию %s", session_id, exc_info=True
            )
            self.disconnect(session_id)

    @property
    def active_sessions(self) -> list[str]:
        """Список активных session_id."""
        return list(self._connections.keys())
