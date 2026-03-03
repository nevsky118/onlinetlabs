# WS listener -> DB persistence для истории событий.

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.models import HistoryEvent

logger = logging.getLogger(__name__)


class HistoryListener:
    """Слушает GNS3 WS notifications, пишет в БД."""

    def __init__(self, ws_url: str, token: str, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._ws_url = ws_url
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
        import websockets

        delay = 1
        max_delay = 60
        while self._running:
            try:
                headers = {"Authorization": f"Bearer {self._token}"}
                async with websockets.connect(self._ws_url, additional_headers=headers) as ws:
                    delay = 1
                    async for raw in ws:
                        parsed = self._parse_event(raw)
                        if parsed and parsed.get("project_id") in self._project_to_session:
                            await self._persist_event(parsed)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("WS listener error, reconnecting in %ds", delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, max_delay)

    def _parse_event(self, raw: str) -> dict | None:
        try:
            msg = json.loads(raw)
            return {
                "event_type": msg.get("event", "unknown"),
                "project_id": msg.get("project_id"),
                "component_id": msg.get("node_id") or msg.get("link_id"),
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
