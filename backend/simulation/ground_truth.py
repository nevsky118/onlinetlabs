"""Storage of the sim-student's true latent regime for honest observer ROC.

Reuses RegimeAnnotation with coder_id="sim-truth", is_gold=True. Written only for
is_simulated sessions (session-level firewall), marked as simulation.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from models.regime_annotation import RegimeAnnotation

SIM_TRUTH_CODER = "sim-truth"


async def record_truth(
    db: AsyncSession, session_id: str, window_index: int, true_regime: str
) -> None:
    """Record the window's true regime as the simulation's gold annotation."""
    db.add(RegimeAnnotation(
        session_id=session_id, coder_id=SIM_TRUTH_CODER, window_index=window_index,
        regime_label=true_regime, is_gold=True,
    ))
    await db.commit()
