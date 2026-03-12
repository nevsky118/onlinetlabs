# HTTP stream listener -> DB persistence для истории событий.

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.models import HistoryEvent

logger = logging.getLogger(__name__)


class HistoryListener:
    """Слушает GNS3 HTTP stream notifications, пишет в БД."""

    def __init__(self, base_url: str, token: str, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._url = f"{base_url}/v3/notifications"
        self._token = token
        self._session_factory = session_factory
        self._project_to_session: dict[str, uuid.UUID] = {}
        self._task: asyncio.Task | None = None
        self._running = False

    def register_session(self, project_id: str, session_id: uuid.UUID) -> None:
        self._project_to_session[project_id] = session_id

    def unregister_session(self, project_id: str) -> None:
        self._project_to_session.pop(project_id, None)

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _listen(self) -> None:
        delay = 1
        max_delay = 60
        headers = {"Authorization": f"Bearer {self._token}"}
        while self._running:
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream("GET", self._url, headers=headers) as resp:
                        resp.raise_for_status()
                        delay = 1
                        async for line in resp.aiter_lines():
                            if not self._running:
                                break
                            parsed = self._parse_event(line)
                            if parsed and parsed.get("project_id") in self._project_to_session:
                                await self._persist_event(parsed)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Stream listener error, reconnecting in %ds", delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, max_delay)

    def _parse_event(self, raw: str) -> dict | None:
        try:
            msg = json.loads(raw)
            event = msg.get("event", {})
            return {
                "event_type": msg.get("action", "unknown"),
                "project_id": event.get("project_id") if isinstance(event, dict) else None,
                "component_id": (event.get("node_id") or event.get("link_id")) if isinstance(event, dict) else None,
                "data": msg,
            }
        except (json.JSONDecodeError, KeyError):
            return None

    async def _persist_event(self, event: dict) -> None:
        session_id = self._project_to_session.get(event["project_id"])
        if not session_id:
            return
        try:
            entry = HistoryEvent(
                session_id=session_id,
                event_type=event["event_type"],
                component_id=event.get("component_id"),
                data=event.get("data", {}),
                timestamp=datetime.now(timezone.utc),
            )
            async with self._session_factory() as db:
                db.add(entry)
                await db.commit()
        except Exception:
            logger.exception("Failed to persist event %s", event.get("event_type"))
