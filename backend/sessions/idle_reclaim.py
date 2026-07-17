"""Idle session reclaimer. Stops nodes after 30 minutes of inactivity.

Frees RAM on gns3-server. The student can restart nodes upon return.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from db.session import async_session
from models.session import LearningSession
from observability.metrics import idle_reclaimed_counter

logger = logging.getLogger(__name__)

IDLE_THRESHOLD_MIN = 30
# Every N seconds, the reclaimer closes sessions inactive for more than 30 minutes.
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
    """Stops nodes of active sessions inactive longer than the idle threshold."""
    cutoff = datetime.now(UTC) - timedelta(minutes=IDLE_THRESHOLD_MIN)
    async with async_session() as db:
        result = await db.execute(select(LearningSession).where(LearningSession.status == "active"))
        sessions = result.scalars().all()

    reclaimed = 0
    for session in sessions:
        last_activity = await _last_activity_at(gns3_client, session)
        if last_activity is None or last_activity > cutoff:
            continue
        gns3_sid = (session.meta or {}).get("gns3_service_session_id")
        if not gns3_sid:
            continue
        try:
            await gns3_client.bulk_node_action(gns3_sid, "stop")
            logger.info(
                "idle_reclaim: stopped nodes session=%s last_activity=%s",
                session.id,
                last_activity.isoformat(),
            )
            try:
                idle_reclaimed_counter.labels(lab_slug=session.lab_slug).inc()
            except Exception:
                pass
            reclaimed += 1
        except Exception:
            logger.exception("idle_reclaim: stop failed session=%s", session.id)
    if reclaimed:
        logger.info("idle_reclaim: %d sessions reclaimed", reclaimed)


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
