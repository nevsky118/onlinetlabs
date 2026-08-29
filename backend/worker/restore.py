"""Restores in-memory session monitors after a restart."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from config import settings
from kit.db import async_session
from models.learning import LearningSession
from sessions.context import build_session_context
from sessions.monitor_registry import SessionMonitorRegistry

logger = logging.getLogger(__name__)


async def restore_session_monitors(monitor_registry: SessionMonitorRegistry) -> int:
    """Restarts the monitor for every live session. Returns how many were restored.

    The registry lives in memory and is lost when the container restarts, so
    without this the active sessions run without proactive interventions until
    their next launch.
    """
    cutoff = datetime.now(tz=UTC) - timedelta(
        hours=settings.learning_analytics.progress_max_duration_hours
    )
    try:
        async with async_session() as db:
            result = await db.execute(
                select(LearningSession).where(
                    LearningSession.status == "active",
                    LearningSession.started_at >= cutoff,
                )
            )
            sessions = result.scalars().all()
    except Exception:
        logger.warning("Failed to load active sessions for monitoring", exc_info=True)
        return 0

    restored = 0
    for session in sessions:
        try:
            ctx = build_session_context(session)
            await monitor_registry.start(session.id, session.user_id, session.lab_slug, ctx)
            restored += 1
        except Exception:
            logger.warning("Failed to restore the SessionMonitor for %s", session.id, exc_info=True)
    if restored:
        logger.info("Session monitors restored: %d", restored)
    return restored
