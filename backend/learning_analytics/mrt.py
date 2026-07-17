"""MRT: операции над точками решения на уровне сессии (censoring при завершении)."""
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from models.intervention_decision import InterventionDecision


async def censor_open_decisions(db: AsyncSession, session_id: str) -> int:
    """Пометить censored=True точки решения сессии с незакрытым spell (exit_ts IS NULL).

    Вызывается при завершении сессии: spell, не закрывшийся до конца сессии,
    правоцензурирован для hazard-модели. Возвращает число помеченных строк.
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
