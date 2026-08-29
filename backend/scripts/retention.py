"""Retention sweep: drops audit rows past their keep window."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete

from config import settings
from db.session import async_session
from models.mcp_audit import MCPAudit

logger = logging.getLogger(__name__)

SWEEP_INTERVAL_SEC = 24 * 3600


async def retention_loop() -> None:
    """Background loop that periodically applies the retention window."""
    while True:
        try:
            await asyncio.sleep(SWEEP_INTERVAL_SEC)
            await sweep_mcp_audit()
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("retention_loop iteration failed")


async def sweep_mcp_audit() -> int:
    """Deletes mcp_audit rows older than the configured window."""
    days = settings.capacity.mcp_audit_retention_days
    cutoff = datetime.now(UTC) - timedelta(days=days)
    async with async_session() as db:
        result = await db.execute(delete(MCPAudit).where(MCPAudit.ts < cutoff))
        await db.commit()
    removed = result.rowcount or 0
    if removed:
        logger.info("retention: %d mcp_audit rows older than %dd removed", removed, days)
    return removed
