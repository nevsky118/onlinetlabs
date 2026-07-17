"""PostgreSQL LISTEN history_events → EventBroker.

Subscribes to the `history_events` NOTIFY channel set up by the alembic
migration `history_events_notify_trigger`. Each NOTIFY payload is a JSON
object with session_id, event_type, component_id, timestamp, data.
Re-publishes as `history.event` envelope to the per-session broker.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime

import asyncpg

from src.events_broker import EventBroker

logger = logging.getLogger(__name__)


class HistoryPgListener:
    def __init__(self, dsn: str, broker: EventBroker) -> None:
        self._dsn = dsn
        self._broker = broker
        self._task: asyncio.Task | None = None
        self._conn: asyncpg.Connection | None = None
        self._stop_event: asyncio.Event = asyncio.Event()
        self._pending_publishes: set[asyncio.Task] = set()

    async def start(self) -> None:
        if self._task is not None:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._conn is not None:
            try:
                await self._conn.close()
            except Exception:
                logger.exception("Error closing PG listener connection")
            self._conn = None
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None

    async def _run(self) -> None:
        backoff = 1
        while not self._stop_event.is_set():
            try:
                self._conn = await asyncpg.connect(self._dsn)
                await self._conn.add_listener("history_events", self._on_notify)
                # Explicitly call LISTEN so the subscription survives a mismatch
                # between asyncpg's internal state and the server after reconnects.
                await self._conn.execute("LISTEN history_events")
                logger.warning(
                    "PG listener subscribed to history_events channel (pid=%s)",
                    getattr(self._conn, "_protocol", None)
                    and getattr(self._conn._protocol, "backend_pid", None),
                )
                backoff = 1
                # Hang here until stop or the connection drops
                while not self._stop_event.is_set():
                    await asyncio.sleep(60)
                    try:
                        await self._conn.fetchval("SELECT 1")
                    except Exception:
                        logger.warning("PG listener detected dropped connection")
                        break
            except asyncio.CancelledError:
                return
            except Exception as exc:
                logger.warning("PG listener error: %s", exc)
            finally:
                if self._conn is not None:
                    try:
                        await self._conn.close()
                    except Exception:
                        pass
                    self._conn = None
            if self._stop_event.is_set():
                return
            await asyncio.sleep(min(30, backoff))
            backoff = min(30, backoff * 2)

    def _on_notify(self, conn, pid, channel, payload) -> None:
        """asyncpg callback that schedules a publish task."""
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            logger.debug(
                "Bad NOTIFY payload (not JSON): %r",
                payload[:100] if isinstance(payload, str) else payload,
            )
            return
        session_id = data.get("session_id")
        if not session_id:
            return
        event = {
            "type": "history.event",
            "timestamp": datetime.now(UTC).isoformat(),
            "payload": {
                "event_type": data.get("event_type"),
                "component_id": data.get("component_id"),
                "data": data.get("data"),
            },
        }
        task = asyncio.create_task(self._broker.publish(session_id, event))
        self._pending_publishes.add(task)
        task.add_done_callback(self._pending_publishes.discard)
