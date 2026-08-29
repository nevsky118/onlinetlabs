"""Idle session reclaimer. Saves node config, stops nodes, marks the session paused."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from config import settings
from kit.db import async_session
from models.learning import LearningSession
from observability.metrics import idle_reclaimed_counter
from sessions.services.persist import persist_volatile_configs

logger = logging.getLogger(__name__)

IDLE_THRESHOLD_MIN = 30
RECLAIM_INTERVAL_SEC = 300


async def idle_reclaim_loop(gns3_client) -> None:
    """Background loop that periodically reclaims idle sessions."""
    while True:
        try:
            await asyncio.sleep(RECLAIM_INTERVAL_SEC)
            await _reclaim_idle_sessions(gns3_client)
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("idle_reclaim_loop iteration failed")


async def _reclaim_idle_sessions(gns3_client) -> None:
    """Pauses active sessions with no student activity past the idle threshold."""
    cutoff = datetime.now(UTC) - timedelta(minutes=IDLE_THRESHOLD_MIN)
    async with async_session() as db:
        result = await db.execute(
            select(LearningSession).where(
                LearningSession.status == "active",
                LearningSession.paused_at.is_(None),
                LearningSession.last_seen_at < cutoff,
            )
        )
        sessions = result.scalars().all()

    reclaimed = 0
    for session in sessions:
        # gns3 topology activity can only spare a session, never condemn one
        gns3_activity = await _last_activity_at(gns3_client, session)
        if gns3_activity is not None and gns3_activity > cutoff:
            continue
        gns3_sid = (session.meta or {}).get("gns3_service_session_id")
        if not gns3_sid:
            continue
        try:
            saved = await persist_volatile_configs(gns3_client, gns3_sid, settings)
            await gns3_client.bulk_node_action(gns3_sid, "stop")
            await _mark_paused(str(session.id))
            logger.info(
                "idle_reclaim: paused session=%s last_seen=%s configs_saved=%d",
                session.id,
                session.last_seen_at.isoformat(),
                saved,
            )
            try:
                idle_reclaimed_counter.labels(lab_slug=session.lab_slug).inc()
            except Exception:
                pass
            reclaimed += 1
        except Exception:
            logger.exception("idle_reclaim: pause failed session=%s", session.id)
    if reclaimed:
        logger.info("idle_reclaim: %d sessions paused", reclaimed)


async def _mark_paused(session_id: str) -> None:
    """Flags the session as paused so its state reads as resumable, not broken."""
    async with async_session() as db:
        await db.execute(
            update(LearningSession)
            .where(LearningSession.id == session_id)
            .values(paused_at=datetime.now(UTC))
        )
        await db.commit()


async def _last_activity_at(gns3_client, session) -> datetime | None:
    """Returns the session's last activity time in gns3, or None if there is none."""
    gns3_sid = (session.meta or {}).get("gns3_service_session_id")
    if not gns3_sid:
        return None
    try:
        data = await gns3_client.get_activity(gns3_sid, limit=1)
    except Exception:
        return None
    events = data.get("events", [])
    if not events:
        return None
    ts_str = events[0].get("timestamp")
    if not ts_str:
        return None
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
