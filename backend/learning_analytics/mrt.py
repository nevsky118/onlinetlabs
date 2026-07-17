"""MRT: session-level operations on decision points (censoring on completion)."""
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from models.intervention_decision import InterventionDecision


async def censor_open_decisions(db: AsyncSession, session_id: str) -> int:
    """Mark censored=True on the session's decision points with an open spell (exit_ts IS NULL).

    Called on session completion: a spell that didn't close before the session ended
    is right-censored for the hazard model. Returns the number of rows marked.
    """
    result = await db.execute(
        update(InterventionDecision)
        .where(
            InterventionDecision.session_id == session_id,
            InterventionDecision.subsequent_exit_ts.is_(None),
        )
        .values(censored=True)
    )
    await db.commit()
    return result.rowcount or 0
