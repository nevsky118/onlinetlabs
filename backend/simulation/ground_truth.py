"""Хранение истинного латентного режима сим-студента для честной observer-ROC.

Реюзит RegimeAnnotation с coder_id="sim-truth", is_gold=True. Пишется только для
is_simulated-сессий (firewall на уровне сессии), помечено как симуляция.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from models.regime_annotation import RegimeAnnotation

SIM_TRUTH_CODER = "sim-truth"


async def record_truth(
    db: AsyncSession, session_id: str, window_index: int, true_regime: str
) -> None:
    """Записать истинный режим окна как gold-аннотацию симуляции."""
    db.add(RegimeAnnotation(
        session_id=session_id, coder_id=SIM_TRUTH_CODER, window_index=window_index,
        regime_label=true_regime, is_gold=True,
    ))
    await db.commit()
