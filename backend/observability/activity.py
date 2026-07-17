"""AgentActivityLog: non-blocking event emission → persist + pub/sub."""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import delete, select

from models.agent_activity_event import AgentActivityEventRow
from observability.models import AgentActivityEvent
from observability.redact import redact

logger = logging.getLogger(__name__)


class AgentActivityLog:
    def __init__(self, db_factory, retention_per_session: int):
        self._db_factory = db_factory
        self._retention = retention_per_session
        self._subs: dict[str, set[asyncio.Queue]] = {}

    def subscribe(self, session_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._subs.setdefault(session_id, set()).add(q)
        return q

    def unsubscribe(self, session_id: str, q: asyncio.Queue) -> None:
        subs = self._subs.get(session_id)
        if subs:
            subs.discard(q)
            if not subs:
                self._subs.pop(session_id, None)

    def emit(self, event: AgentActivityEvent) -> None:
        """Non-blocking: redacts, publishes to subscribers, schedules the write."""
        try:
            event.detail = redact(event.detail)
            for q in list(self._subs.get(event.session_id, ())):
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    pass  # slow observer — drop the frame
            asyncio.create_task(self._persist(event))
        except Exception:
            logger.warning("activity emit failed", exc_info=True)

    async def _persist(self, event: AgentActivityEvent) -> None:
        try:
            async with self._db_factory() as db:
                db.add(
                    AgentActivityEventRow(
                        id=event.id,
                        session_id=event.session_id,
                        user_id=event.user_id,
                        ts=event.ts,
                        source=event.source.value,
                        kind=event.kind.value,
                        agent=event.agent,
                        severity=event.severity,
                        summary=event.summary,
                        detail=event.detail,
                    )
                )
                await db.commit()
                await self._prune(db, event.session_id)
        except Exception:
            logger.warning("activity persist failed", exc_info=True)

    async def _prune(self, db, session_id: str) -> None:
        """Best-effort trim down to the retention of the session's latest events."""
        try:
            stmt = (
                select(AgentActivityEventRow.id)
                .where(AgentActivityEventRow.session_id == session_id)
                .order_by(AgentActivityEventRow.ts.desc())
                .offset(self._retention)
            )
            stale = [r for r in (await db.execute(stmt)).scalars().all()]
            if stale:
                await db.execute(
                    delete(AgentActivityEventRow).where(AgentActivityEventRow.id.in_(stale))
                )
                await db.commit()
        except Exception:
            logger.warning("activity prune failed", exc_info=True)

    async def history(
        self, session_id: str, since: datetime | None, limit: int
    ) -> list[AgentActivityEvent]:
        async with self._db_factory() as db:
            stmt = select(AgentActivityEventRow).where(
                AgentActivityEventRow.session_id == session_id
            )
            if since is not None:
                stmt = stmt.where(AgentActivityEventRow.ts > since)
            stmt = stmt.order_by(AgentActivityEventRow.ts.asc()).limit(limit)
            rows = (await db.execute(stmt)).scalars().all()
            return [
                AgentActivityEvent(
                    id=r.id,
                    session_id=r.session_id,
                    user_id=r.user_id,
                    ts=r.ts,
                    source=r.source,
                    kind=r.kind,
                    agent=r.agent,
                    severity=r.severity,
                    summary=r.summary,
                    detail=r.detail,
                )
                for r in rows
            ]
