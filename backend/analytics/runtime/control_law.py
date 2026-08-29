"""The intervention decision, as one function.

Every gate the loop applies lives here in a fixed order, so the arm contract
cannot be bypassed by a branch that returns early. `Decision.reason` carries the
provenance that callers used to hardcode at the log site.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from analytics.runtime.process_state import ProcessRegime, is_bad
from config.config_model import LearningAnalyticsConfig
from experiment.assignment import ControlArm

Action = Literal["intervene", "withhold", "skip"]


@dataclass(frozen=True)
class Decision:
    """What the loop should do at this decision point, and why.

    intervene -- deliver; withhold -- record the point but deliver nothing
    (this is the measurement the hazard model needs); skip -- not a decision
    point at all, record nothing.
    """

    action: Action
    reason: str


def should_intervene(
    *,
    regime: ProcessRegime,
    dwell: float,
    arm: ControlArm,
    last_intervention_at: datetime | None,
    cfg: LearningAnalyticsConfig,
    now: datetime,
    mrt_threshold: float | None = None,
    hold_draw: float | None = None,
) -> Decision:
    """Decides whether to intervene.

    mrt_threshold -- the spell's jittered T_k when MRT is running; None uses the
    configured T_k for the regime. hold_draw -- a U[0,1) draw, supplied only under
    MRT so the randomization stays testable and the caller owns the RNG.

    Gate order is the contract: regime, dwell, cooldown, arm, then MRT. The arm
    is checked BEFORE the MRT draw, so an open-arm session can never be handed a
    real intervention by the randomizer.
    """
    if not is_bad(regime):
        return Decision("skip", "productive")

    threshold = (
        mrt_threshold if mrt_threshold is not None else cfg.dwell_thresholds.get(regime.value, 0.0)
    )
    if dwell < threshold:
        return Decision("skip", "dwell_below_threshold")

    if not cfg.enabled:
        return Decision("skip", "interventions_disabled")

    if last_intervention_at is not None:
        elapsed = (now - last_intervention_at).total_seconds()
        if elapsed < cfg.cooldown_period:
            return Decision("skip", "cooldown")

    if arm == ControlArm.OPEN:
        return Decision("withhold", "open_arm")

    if hold_draw is not None and hold_draw < cfg.mrt_hold_probability:
        return Decision("withhold", "mrt_hold")

    return Decision("intervene", "mrt_intervene" if hold_draw is not None else "threshold_reached")
