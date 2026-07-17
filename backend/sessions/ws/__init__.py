"""WebSocket for sessions. Unified gateway and gns3 event forwarder."""

from sessions.ws.events import forward_session_events
from sessions.ws.gateway import (
    WebSocketGateway,
    close_all_connections,
    register_connection,
    unregister_connection,
)

__all__ = [
    "WebSocketGateway",
    "close_all_connections",
    "forward_session_events",
    "register_connection",
    "unregister_connection",
]
