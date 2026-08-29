"""Session reaper: ends sessions past their deadline and frees what they held."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select

from config import settings
from kit.db import async_session
from models.learning import LearningSession
from sessions.services.lifecycle import _mark_ended_and_finalize
from sessions.services.persist import persist_volatile_configs

logger = logging.getLogger(__name__)

REAP_INTERVAL_SEC = 600
# Provisioning takes about half a minute. A row still in that state much later
# is the debris of a crash, and it holds the learner's only slot for this lab.
STALE_PROVISIONING_MIN = 15


async def session_reaper_loop(gns3_client, monitor_registry) -> None:
    """Background loop that periodically ends expired sessions."""
    while True:
        try:
            await asyncio.sleep(REAP_INTERVAL_SEC)
            await reap_expired_sessions(gns3_client, monitor_registry)
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("session_reaper_loop iteration failed")


async def reap_expired_sessions(gns3_client, monitor_registry) -> int:
    """Ends sessions past their deadline, and provisioning rows left by a crash."""
    now = datetime.now(UTC)
    stale_provisioning = now - timedelta(minutes=STALE_PROVISIONING_MIN)
    async with async_session() as db:
        rows = (
            (
                await db.execute(
                    select(LearningSession).where(
                        LearningSession.status.in_(("active", "provisioning")),
                        or_(
                            and_(
                                LearningSession.expires_at.is_not(None),
                                LearningSession.expires_at < now,
                            ),
                            and_(
                                LearningSession.status == "provisioning",
                                LearningSession.started_at < stale_provisioning,
                            ),
                        ),
                    )
                )
            )
            .scalars()
            .all()
        )

    ended = 0
    for session in rows:
        try:
            await _end_one(session, gns3_client, monitor_registry)
            ended += 1
        except Exception:
            logger.exception("session_reaper: failed to end %s", session.id)
    if ended:
        logger.info("session_reaper: %d sessions ended", ended)
    return ended


async def _end_one(session, gns3_client, monitor_registry) -> None:
    """Stops the monitor, saves config, finalizes the row, tears down gns3."""
    await monitor_registry.stop(str(session.id))
    gns3_sid = (session.meta or {}).get("gns3_service_session_id")
    if gns3_sid:
        try:
            await persist_volatile_configs(gns3_client, gns3_sid, settings)
        except Exception:
            logger.warning("session_reaper: save failed for %s", session.id, exc_info=True)
    async with async_session() as db:
        row = await db.get(LearningSession, session.id)
        if row is not None:
            await _mark_ended_and_finalize(db, row, status="ended")
    if gns3_sid:
        try:
            await gns3_client.delete_session(gns3_sid)
        except Exception:
            logger.warning("session_reaper: teardown failed for %s", session.id, exc_info=True)
