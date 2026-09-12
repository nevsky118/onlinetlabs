"""Age-based purge of recorded console traffic."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from src.db.models import ConsoleChunk, ConsoleCommand, SessionStatus
from src.db.models import Session as SessionModel

logger = logging.getLogger(__name__)

_BATCH_SIZE = 10_000
_BATCH_PAUSE_SEC = 0.5

# Daily sweep, first one immediately.
SWEEP_INTERVAL_SEC = 24 * 3600


async def run_console_retention(
    db_factory, retention_window: timedelta, interval_sec: float = SWEEP_INTERVAL_SEC
) -> None:
    """Purges aged console rows at startup, then once per interval."""
    while True:
        try:
            removed = await purge_console_history(db_factory, retention_window)
            if removed:
                logger.info("console retention: purged %d rows", removed)
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("console retention sweep failed")
        try:
            await asyncio.sleep(interval_sec)
        except asyncio.CancelledError:
            return


async def purge_console_history(db_factory, older_than: timedelta) -> int:
    """Deletes aged console rows; active sessions are kept."""
    cutoff = datetime.now(UTC) - older_than
    deleted = 0
    for model in (ConsoleChunk, ConsoleCommand):
        deleted += await _purge_model(db_factory, model, cutoff)
    return deleted


async def _purge_model(db_factory, model, cutoff: datetime) -> int:
    """Deletes one table's doomed rows in batches, committing per batch."""
    live_sessions = select(SessionModel.id).where(SessionModel.status == SessionStatus.ACTIVE)
    removed = 0
    while True:
        doomed = (
            select(model.id)
            .where(model.ts < cutoff, model.session_id.not_in(live_sessions))
            .limit(_BATCH_SIZE)
            .scalar_subquery()
        )
        async with db_factory() as db:
            result = await db.execute(delete(model).where(model.id.in_(doomed)))
            await db.commit()
        batch = result.rowcount or 0
        removed += batch
        if batch < _BATCH_SIZE:
            break
        await asyncio.sleep(_BATCH_PAUSE_SEC)
    return removed
