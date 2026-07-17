"""Reproducibility bundle: anonymized export of real MRT data for re-analysis."""
import hashlib

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.intervention_decision import InterventionDecision
from models.regime_annotation import RegimeAnnotation
from models.session import LearningSession
from models.user import User


def _anon(value: str) -> str:
    """Stable anonymous id (sha256, 12 hex) -- consistent across tables."""
    return hashlib.sha256(value.encode()).hexdigest()[:12]


async def build_reproducibility_bundle(db: AsyncSession) -> dict:
    """Bundle of real MRT data for independent re-analysis.

    FIREWALL: data from is_simulated users is EXCLUDED -- simulation runs never
    flow into "real results". Personal ids are replaced with hashes.
    """
    sim_users = select(User.id).where(User.is_simulated.is_(True)).scalar_subquery()
    sim_sessions = (
        select(LearningSession.id)
        .where(LearningSession.user_id.in_(sim_users))
        .scalar_subquery()
    )
    decisions = (await db.execute(
        select(InterventionDecision).where(InterventionDecision.user_id.notin_(sim_users))
    )).scalars().all()
    annotations = (await db.execute(
        select(RegimeAnnotation).where(RegimeAnnotation.session_id.notin_(sim_sessions))
    )).scalars().all()
    gold = (await db.execute(
        select(func.count()).select_from(RegimeAnnotation).where(
            RegimeAnnotation.is_gold.is_(True),
            RegimeAnnotation.session_id.notin_(sim_sessions),
        )
    )).scalar_one()
    return {
        "intervention_decisions": [
            {
                "session": _anon(d.session_id),
                "user": _anon(d.user_id),
                "spell_id": d.spell_id,
                "ts": d.ts.isoformat() if d.ts else None,
                "regime": d.regime,
                "dwell_seconds": d.dwell_seconds,
                "t_k_applied": d.t_k_applied,
                "assignment": d.assignment,
                "subsequent_exit_ts": (
                    d.subsequent_exit_ts.isoformat() if d.subsequent_exit_ts else None
                ),
                "censored": d.censored,
            }
            for d in decisions
        ],
        "regime_annotations": [
            {
                "session": _anon(a.session_id),
                "coder_id": a.coder_id,
                "window_index": a.window_index,
                "regime_label": a.regime_label,
                "is_gold": a.is_gold,
            }
            for a in annotations
        ],
        "gold_label_count": gold,
    }
