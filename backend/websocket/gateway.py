"""WebSocket gateway — управление соединениями и доставка интервенций."""

import logging
from datetime import datetime, timezone

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketGateway:
    """Управление WebSocket-соединениями по session_id."""

    def __init__(self):
        """Инициализация пула соединений."""
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Зарегистрировать WebSocket для сессии."""
        await websocket.accept()
        self._connections[session_id] = websocket

    def disconnect(self, session_id: str) -> None:
        """Удалить WebSocket сессии."""
        self._connections.pop(session_id, None)

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
            logger.warning("Не удалось отправить интервенцию в сессию %s", session_id, exc_info=True)
            self.disconnect(session_id)

    @property
    def active_sessions(self) -> list[str]:
        """Список активных session_id."""
        return list(self._connections.keys())
