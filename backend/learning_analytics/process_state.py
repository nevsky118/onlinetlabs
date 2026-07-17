"""State variable of the controlled process: discrete regime + dwell-time."""

from datetime import datetime
from enum import Enum


class ProcessRegime(str, Enum):
    """Process regime: productive or struggle of type k (mirrors StruggleType)."""

    PRODUCTIVE = "productive"
    STUCK_ON_STEP = "stuck_on_step"
    REPEATING_ERRORS = "repeating_errors"
    IDLE = "idle"
    TRIAL_AND_ERROR = "trial_and_error"


def analysis_to_regime(analysis) -> ProcessRegime:
    """Derive state from the identifier's result. No struggle → productive."""
    if not analysis.struggle_detected or analysis.struggle_type is None:
        return ProcessRegime.PRODUCTIVE
    return ProcessRegime(analysis.struggle_type.value)


def is_bad(regime: ProcessRegime) -> bool:
    """Bad regime = any struggle (not productive)."""
    return regime != ProcessRegime.PRODUCTIVE


class DwellTracker:
    """Tracks continuous time spent in one regime. Regime change resets it."""

    def __init__(self) -> None:
        self._regime: ProcessRegime | None = None
        self._since: datetime | None = None

    @property
    def current_regime(self) -> ProcessRegime | None:
        return self._regime

    def observe(self, regime: ProcessRegime, now: datetime) -> float:
        """Record the regime at time now, return dwell_seconds in the current regime."""
        if regime != self._regime:
            self._regime = regime
            self._since = now
            return 0.0
        return (now - self._since).total_seconds()
