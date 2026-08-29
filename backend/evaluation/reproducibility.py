"""Reproducibility bundle: pseudonymous export of real MRT data for re-analysis."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.intervention_decision import InterventionDecision
from models.regime_annotation import RegimeAnnotation
from models.session import LearningSession
from models.user import User
from research.pseudonyms import pseudonym_map, research_id_map

# Every key this bundle may carry. A column outside it must not reach an export.
BUNDLE_IDENTIFIER_KEYS = frozenset({"session", "user"})


async def build_reproducibility_bundle(db: AsyncSession) -> dict:
    """Bundle of real MRT data for independent re-analysis.

    FIREWALL: data from is_simulated users is EXCLUDED -- simulation runs never
    flow into "real results". Identities are replaced by study pseudonyms and
    per-session research ids, both random and stored, never derived.
    """
    sim_users = select(User.id).where(User.is_simulated.is_(True)).scalar_subquery()
    sim_sessions = (
        select(LearningSession.id).where(LearningSession.user_id.in_(sim_users)).scalar_subquery()
    )
    decisions = (
        (
            await db.execute(
                select(InterventionDecision).where(InterventionDecision.user_id.notin_(sim_users))
            )
        )
        .scalars()
        .all()
    )
    annotations = (
        (
            await db.execute(
                select(RegimeAnnotation).where(RegimeAnnotation.session_id.notin_(sim_sessions))
            )
        )
        .scalars()
        .all()
    )
    gold = (
        await db.execute(
            select(func.count())
            .select_from(RegimeAnnotation)
            .where(
                RegimeAnnotation.is_gold.is_(True),
                RegimeAnnotation.session_id.notin_(sim_sessions),
            )
        )
    ).scalar_one()
    pseudonyms = await pseudonym_map(db, [d.user_id for d in decisions])
    research_ids = await research_id_map(
        db, [d.session_id for d in decisions] + [a.session_id for a in annotations]
    )
    return {
        "intervention_decisions": [
            {
                "session": research_ids.get(d.session_id),
                "user": pseudonyms.get(d.user_id),
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
                "session": research_ids.get(a.session_id),
                "coder_id": a.coder_id,
                "window_index": a.window_index,
                "regime_label": a.regime_label,
                "is_gold": a.is_gold,
            }
            for a in annotations
        ],
        "gold_label_count": gold,
    }
