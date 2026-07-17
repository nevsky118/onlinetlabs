# Lazy WS listener + ring buffer of GNS3 logs.

from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import UTC, datetime

from mcp_sdk.models import ErrorEntry, LogEntry, LogLevel

logger = logging.getLogger(__name__)


class LogBuffer:
    """Ring buffer of logs from GNS3 WS notifications."""

    def __init__(self, max_entries: int = 500, inactivity_timeout: float = 300.0) -> None:
        self._max_entries = max_entries
        self._inactivity_timeout = inactivity_timeout
        self._entries: deque[LogEntry] = deque(maxlen=max_entries)
        self._ws_task: asyncio.Task | None = None
        self._connected = False
        self._last_activity: float = 0

    @property
    def connected(self) -> bool:
        return self._connected

    def _add_entry(self, level: LogLevel, message: str, source: str = "gns3") -> None:
        """Add an entry to the buffer. Called from the WS listener."""
        entry = LogEntry(
            timestamp=datetime.now(tz=UTC),
            level=level,
            source=source,
            message=message,
        )
        self._entries.append(entry)

    async def ensure_connected(self, ws_url: str, jwt: str | None = None) -> None:
        """Connect to WS if not already connected."""
        if self._connected and self._ws_task and not self._ws_task.done():
            return
        self._connected = True
        self._ws_task = asyncio.create_task(self._listen(ws_url, jwt))

    async def _listen(self, ws_url: str, jwt: str | None = None) -> None:
        """Background WS listener. Filters log.* events."""
        import json
        from urllib.parse import urlparse, urlunparse

        try:
            import websockets

            # GNS3 WebSocket auth requires the token as a query parameter ?token=...
            # (not an Authorization: Bearer header), see get_current_active_user_from_websocket.
            if jwt:
                parsed = urlparse(ws_url)
                qs = f"token={jwt}"
                ws_url = urlunparse(parsed._replace(query=qs))
            async with websockets.connect(ws_url) as ws:
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                        event = msg.get("event", "")
                        if event == "log.error":
                            self._add_entry(LogLevel.ERROR, msg.get("message", ""))
                        elif event == "log.warning":
                            self._add_entry(LogLevel.WARNING, msg.get("message", ""))
                        elif event == "log.info":
                            self._add_entry(LogLevel.INFO, msg.get("message", ""))
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception:
            logger.exception("WS listener error")
        finally:
            self._connected = False

    def get_errors(self, since: datetime | None = None) -> list[ErrorEntry]:
        """Errors and warnings from the buffer."""
        result = []
        for entry in self._entries:
            if entry.level not in (LogLevel.ERROR, LogLevel.WARNING):
                continue
            if since and entry.timestamp < since:
                continue
            result.append(
                ErrorEntry(
                    timestamp=entry.timestamp,
                    level=entry.level,
                    message=entry.message,
                )
            )
        return result

    def get_logs(self, level: LogLevel = LogLevel.ALL, limit: int = 100) -> list[LogEntry]:
        """Logs from the buffer filtered by level."""
        if level == LogLevel.ALL:
            entries = list(self._entries)
        else:
            entries = [entry for entry in self._entries if entry.level == level]
        return entries[-limit:]

    async def close(self) -> None:
        """Stop the WS listener, clear the buffer."""
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        self._entries.clear()
        self._connected = False
