"""GNS3 v3 WS proxy.

Maintains persistent WebSocket subscriptions to /v3/projects/{pid}/notifications.
Translates GNS3 events to broker format and republishes to EventBroker.
On disconnect, reconnects with exponential backoff (1s -> 2s -> 4s -> 8s -> max 30s),
emitting stream.degraded on disconnect and stream.restored on success.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid as uuid_module
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import redis.asyncio as aioredis
import websockets

from src.events_broker import EventBroker

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from src.clients.admin import GNS3AdminClient

logger = logging.getLogger(__name__)

# Actions that get persisted to history_events for the activity feed.
HISTORY_ACTIONS = (
    "node.created",
    "node.updated",
    "node.deleted",
    "link.created",
    "link.deleted",
)


class Gns3WsProxy:
    # 1h lock TTL — renewed every 30 min by heartbeat.
    _LOCK_TTL_SECONDS = 3600
    _HEARTBEAT_INTERVAL_SECONDS = 1800

    def __init__(
        self,
        broker: EventBroker,
        gns3_url: str,
        admin_client: GNS3AdminClient,
        redis_url: str | None = None,
        db_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._broker = broker
        self._gns3_url = gns3_url
        self._admin_client = admin_client
        self._db_factory = db_factory
        self._tasks: dict[str, asyncio.Task] = {}
        self._heartbeat_tasks: dict[str, asyncio.Task] = {}
        # redis_url can be omitted only in unit tests. In prod main.py passes it in.
        self._redis = aioredis.from_url(redis_url, decode_responses=True) if redis_url else None

    def _lock_key(self, project_id: str) -> str:
        return f"lock:ws_proxy:{project_id}"

    def _backoff_delay(self, attempt: int) -> int:
        """1s -> 2s -> 4s -> 8s -> 16s -> max 30s."""
        if attempt == 0:
            return 1
        return min(30, 2**attempt)

    async def start_project(self, project_id: str, session_id: str) -> None:
        """Starts a forwarder for project_id, publishing to the session_id channel.

        Takes a distributed Redis lock so that each project's upstream WS is held
        by only one gns3-service instance. Otherwise broker.publish would be
        duplicated across multiple replicas.
        """
        if project_id in self._tasks:
            return
        if self._redis is not None:
            try:
                locked = await self._redis.set(
                    self._lock_key(project_id),
                    str(session_id),
                    nx=True,
                    ex=self._LOCK_TTL_SECONDS,
                )
            except Exception:
                logger.exception("ws_proxy: lock acquire failed for %s", project_id)
                locked = False
            if not locked:
                logger.info(
                    "ws_proxy: %s already owned by another instance, skip",
                    project_id,
                )
                return
        logger.info(
            "ws_proxy: starting forwarder for project=%s session=%s", project_id, session_id
        )
        self._tasks[project_id] = asyncio.create_task(
            self._supervised_forward(project_id, session_id)
        )
        if self._redis is not None:
            self._heartbeat_tasks[project_id] = asyncio.create_task(self._heartbeat(project_id))

    async def _heartbeat(self, project_id: str) -> None:
        while True:
            try:
                await asyncio.sleep(self._HEARTBEAT_INTERVAL_SECONDS)
                if self._redis is None:
                    return
                await self._redis.expire(self._lock_key(project_id), self._LOCK_TTL_SECONDS)
            except asyncio.CancelledError:
                return
            except Exception:
                logger.exception("ws_proxy heartbeat failed for %s", project_id)

    async def stop_all(self) -> None:
        """Cleanly stop all WS forwarders on service shutdown.

        Iterates over a copy of the keys via a public snapshot so that main.py
        doesn't reach into the private `_tasks`.
        """
        for project_id in list(self._tasks.keys()):
            await self.stop_project(project_id)

    async def stop_project(self, project_id: str) -> None:
        task = self._tasks.pop(project_id, None)
        if task is not None:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        hb = self._heartbeat_tasks.pop(project_id, None)
        if hb is not None:
            hb.cancel()
            try:
                await hb
            except (asyncio.CancelledError, Exception):
                pass
        if self._redis is not None:
            try:
                await self._redis.delete(self._lock_key(project_id))
            except Exception:
                logger.exception("ws_proxy: lock release failed for %s", project_id)

    async def _supervised_forward(self, project_id: str, session_id: str) -> None:
        attempt = 0
        while True:
            try:
                if attempt > 0:
                    await self._publish_envelope(
                        session_id,
                        "stream.degraded",
                        {"reason": f"reconnect attempt {attempt}"},
                    )
                await self._forward_loop(project_id, session_id)
                # Normal exit from forward_loop — upstream closed gracefully
                attempt = 0
            except asyncio.CancelledError:
                return
            except Exception as exc:
                logger.warning("WS proxy %s error: %s", project_id, exc)
            attempt += 1
            await asyncio.sleep(self._backoff_delay(attempt))

    async def _iter_messages(self, project_id: str) -> AsyncIterator[str]:
        """Connects to the GNS3 WS and yields raw JSON messages.

        GNS3 v3 requires an admin JWT in the ?token= query parameter. It rejects
        a standard Authorization header with 403.
        """
        token = self._admin_client.token
        ws_url = (
            self._gns3_url.replace("http://", "ws://").replace("https://", "wss://")
            + f"/v3/projects/{project_id}/notifications/ws"
            + f"?token={token}"
        )
        async with websockets.connect(
            ws_url,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=10,
        ) as ws:
            async for raw in ws:
                yield raw if isinstance(raw, str) else raw.decode("utf-8", errors="ignore")

    async def _forward_loop(self, project_id: str, session_id: str) -> None:
        async for raw in self._iter_messages(project_id):
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                logger.debug("Bad JSON from GNS3 WS: %r", raw[:100])
                continue

            action = msg.get("action", "")
            gns_event = msg.get("event", {}) if isinstance(msg.get("event"), dict) else {}

            if action in HISTORY_ACTIONS:
                await self._persist_history(session_id, action, gns_event)

            event = self._translate(action, gns_event)
            if event is not None:
                await self._broker.publish(session_id, event)

    async def _persist_history(self, session_id: str, action: str, gns_event: dict) -> None:
        if self._db_factory is None:
            return
        try:
            from src.db.models import HistoryEvent

            component_id = gns_event.get("node_id") or gns_event.get("link_id")
            entry = HistoryEvent(
                session_id=uuid_module.UUID(session_id),
                event_type=action,
                component_id=component_id,
                data=gns_event,
                timestamp=datetime.now(UTC),
            )
            async with self._db_factory() as db:
                db.add(entry)
                await db.commit()
        except Exception:
            logger.exception(
                "Failed to persist history event %s for session %s", action, session_id
            )

    def _translate(self, action: str, gns_event: dict) -> dict | None:
        """Translate GNS3 v3 notification to broker event envelope.

        Returns None for unrecognized events.
        """
        ts = datetime.now(UTC).isoformat()

        if action == "node.updated":
            return {
                "type": "node.status_changed",
                "timestamp": ts,
                "payload": {
                    "node_id": gns_event.get("node_id"),
                    "status": gns_event.get("status"),
                },
            }
        if action in ("link.created", "link.deleted", "node.created", "node.deleted"):
            return {
                "type": "history.event",
                "timestamp": ts,
                "payload": {
                    "event_type": action,
                    "component_id": gns_event.get("link_id") or gns_event.get("node_id"),
                    "data": gns_event,
                },
            }
        return None

    async def _publish_envelope(self, session_id: str, event_type: str, payload: dict) -> None:
        await self._broker.publish(
            session_id,
            {
                "type": event_type,
                "timestamp": datetime.now(UTC).isoformat(),
                "payload": payload,
            },
        )
