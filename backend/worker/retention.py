"""Retention sweep: drops audit rows past their keep window."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from config import settings
from kit.db import async_session
from models.audit import MCPAudit

logger = logging.getLogger(__name__)

SWEEP_INTERVAL_SEC = 24 * 3600
_BATCH_SIZE = 10_000
_BATCH_PAUSE_SEC = 0.5


async def retention_loop() -> None:
    """Background loop that applies the retention window, starting at boot.

    Sweeping only after the first interval means a deploy cadence shorter than
    the interval never sweeps at all.
    """
    while True:
        try:
            await sweep_mcp_audit()
            await asyncio.sleep(SWEEP_INTERVAL_SEC)
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("retention_loop iteration failed")


async def sweep_mcp_audit() -> int:
    """Deletes mcp_audit rows older than the configured window, in batches.

    One unbounded DELETE after downtime would write gigabytes of WAL in a single
    transaction and block vacuum on the table it is trying to shrink.
    """
    days = settings.capacity.mcp_audit_retention_days
    cutoff = datetime.now(UTC) - timedelta(days=days)
    removed = 0
    while True:
        doomed = (
            select(MCPAudit.id).where(MCPAudit.ts < cutoff).limit(_BATCH_SIZE).scalar_subquery()
        )
        async with async_session() as db:
            result = await db.execute(delete(MCPAudit).where(MCPAudit.id.in_(doomed)))
            await db.commit()
        batch = result.rowcount or 0
        removed += batch
        if batch < _BATCH_SIZE:
            break
        await asyncio.sleep(_BATCH_PAUSE_SEC)
    if removed:
        logger.info("retention: %d mcp_audit rows older than %dd removed", removed, days)
    return removed
