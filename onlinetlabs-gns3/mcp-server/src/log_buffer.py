# Ленивый WS-слушатель + кольцевой буфер логов GNS3.

from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime, timezone

from onlinetlabs_mcp_sdk.models import ErrorEntry, LogEntry, LogLevel

logger = logging.getLogger(__name__)


class LogBuffer:
    """Кольцевой буфер логов из GNS3 WS notifications."""

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
        """Добавить запись в буфер. Вызывается из WS listener."""
        entry = LogEntry(
            timestamp=datetime.now(tz=timezone.utc),
            level=level,
            source=source,
            message=message,
        )
        self._entries.append(entry)

    async def ensure_connected(self, ws_url: str, jwt: str | None = None) -> None:
        """Подключиться к WS если ещё не подключены."""
        if self._connected and self._ws_task and not self._ws_task.done():
            return
        self._connected = True
        self._ws_task = asyncio.create_task(self._listen(ws_url, jwt))

    async def _listen(self, ws_url: str, jwt: str | None = None) -> None:
        """Фоновый WS listener. Фильтрует log.* события."""
        import json
        try:
            import websockets
            headers = {}
            if jwt:
                headers["Authorization"] = f"Bearer {jwt}"
            async with websockets.connect(ws_url, additional_headers=headers) as ws:
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
        """Ошибки и предупреждения из буфера."""
        result = []
        for entry in self._entries:
            if entry.level not in (LogLevel.ERROR, LogLevel.WARNING):
                continue
            if since and entry.timestamp < since:
                continue
            result.append(ErrorEntry(
                timestamp=entry.timestamp,
                level=entry.level,
                message=entry.message,
            ))
        return result

    def get_logs(self, level: LogLevel = LogLevel.ALL, limit: int = 100) -> list[LogEntry]:
        """Логи из буфера с фильтрацией по уровню."""
        if level == LogLevel.ALL:
            entries = list(self._entries)
        else:
            entries = [entry for entry in self._entries if entry.level == level]
        return entries[-limit:]

    async def close(self) -> None:
        """Остановить WS listener, очистить буфер."""
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        self._entries.clear()
        self._connected = False
