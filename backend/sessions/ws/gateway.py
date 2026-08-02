"""WebSocket gateway for connection management and intervention delivery.

Combines per-session connections for interventions with a global registry
of all active sockets for graceful shutdown (forward gns3 events + interventions).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import WebSocket

logger = logging.getLogger(__name__)

_active_connections: set[WebSocket] = set()


def register_connection(ws: WebSocket) -> None:
    """Adds the socket to the global registry of active connections."""
    _active_connections.add(ws)


def unregister_connection(ws: WebSocket) -> None:
    """Removes the socket from the global registry of active connections."""
    _active_connections.discard(ws)


async def close_all_connections(timeout: float = 5.0) -> None:
    """Closes all active client WS connections with code 1012 (service restart)."""
    for ws in list(_active_connections):
        try:
            await ws.close(code=1012)
        except Exception:
            pass
    await asyncio.sleep(min(0.5, timeout))
    _active_connections.clear()


class WebSocketGateway:
    """Manages WebSocket connections by session_id for interventions and observations."""

    def __init__(self):
        """Stores the active WebSocket connections per session identifier."""
        self._connections: dict[str, set[WebSocket]] = {}
        self._observers: dict[str, set[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Registers a WebSocket for the session.

        A session holds a set, not one slot: a second tab used to evict the first
        and leave it registered but unreachable.
        """
        await websocket.accept()
        self._connections.setdefault(session_id, set()).add(websocket)
        register_connection(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket | None = None) -> None:
        """Removes the session's WebSocket. If websocket is given, removes only that socket."""
        sockets = self._connections.get(session_id)
        if not sockets:
            return
        doomed = {websocket} & sockets if websocket is not None else set(sockets)
        for ws in doomed:
            sockets.discard(ws)
            unregister_connection(ws)
        if not sockets:
            self._connections.pop(session_id, None)

    async def send_intervention(self, session_id: str, intervention_data: dict) -> None:
        """Sends an intervention to every socket the student has open for the session."""
        sockets = self._connections.get(session_id)
        if not sockets:
            logger.warning("WebSocket not found for session %s", session_id)
            return

        payload = {
            "type": "intervention",
            "timestamp": datetime.now(tz=UTC).isoformat(),
            **intervention_data,
        }
        for websocket in list(sockets):
            try:
                await websocket.send_json(payload)
            except Exception:
                logger.warning(
                    "Failed to send an intervention to session %s", session_id, exc_info=True
                )
                self.disconnect(session_id, websocket)

    def connect_observer(self, session_id: str, websocket: WebSocket) -> None:
        """Connects an observer for the session's activity events."""
        self._observers.setdefault(session_id, set()).add(websocket)
        register_connection(websocket)

    def disconnect_observer(self, session_id: str, websocket: WebSocket) -> None:
        """Disconnects the observer from the session."""
        observers = self._observers.get(session_id)
        if observers:
            observers.discard(websocket)
            if not observers:
                self._observers.pop(session_id, None)
        unregister_connection(websocket)

    def observers(self, session_id: str) -> set[WebSocket]:
        """Returns the set of the session's observers (empty if none)."""
        return self._observers.get(session_id, set())

    @property
    def active_sessions(self) -> list[str]:
        """List of active session_id values."""
        return [sid for sid, sockets in self._connections.items() if sockets]
