"""IRR pipeline: storing annotator labels, Cohen's kappa, gold-count."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from evaluation.real_loader import cohens_kappa
from models.regime_annotation import RegimeAnnotation


async def save_annotation(
    db: AsyncSession, session_id: str, coder_id: str, window_index: int,
    regime_label: str, is_gold: bool = False,
) -> None:
    """Save a window's label from an annotator (or adjudicated gold if is_gold=True)."""
    db.add(RegimeAnnotation(
        session_id=session_id, coder_id=coder_id, window_index=window_index,
        regime_label=regime_label, is_gold=is_gold,
    ))
    await db.commit()


async def _labels_by_window(db: AsyncSession, session_id: str, coder_id: str) -> dict[int, str]:
    rows = (await db.execute(
        select(RegimeAnnotation).where(
            RegimeAnnotation.session_id == session_id,
            RegimeAnnotation.coder_id == coder_id,
        )
    )).scalars().all()
    return {r.window_index: r.regime_label for r in rows}


async def inter_rater_kappa(
    db: AsyncSession, session_id: str, coder_a: str, coder_b: str
) -> float:
    """Cohen's kappa between two annotators over shared (aligned) session windows."""
    a = await _labels_by_window(db, session_id, coder_a)
    b = await _labels_by_window(db, session_id, coder_b)
    shared = sorted(set(a) & set(b))
    return cohens_kappa([a[i] for i in shared], [b[i] for i in shared])


async def gold_label_count(db: AsyncSession, session_id: str | None = None) -> int:
    """Count of adjudicated-gold annotations (optionally scoped to one session)."""
    stmt = select(func.count()).select_from(RegimeAnnotation).where(
        RegimeAnnotation.is_gold.is_(True)
    )
    if session_id is not None:
        stmt = stmt.where(RegimeAnnotation.session_id == session_id)
    return (await db.execute(stmt)).scalar_one()
