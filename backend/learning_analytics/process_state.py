"""Переменная состояния управляемого процесса: дискретный режим + dwell-time."""

from datetime import datetime
from enum import Enum

from agents.analytics.models import StruggleType


class ProcessRegime(str, Enum):
    """Режим процесса: продуктивный либо затруднение типа k (зеркалит StruggleType)."""

    PRODUCTIVE = "productive"
    STUCK_ON_STEP = "stuck_on_step"
    REPEATING_ERRORS = "repeating_errors"
    IDLE = "idle"
    TRIAL_AND_ERROR = "trial_and_error"


def analysis_to_regime(analysis) -> ProcessRegime:
    """Оценка состояния из результата идентификатора. Без затруднения — продуктивный."""
    if not analysis.struggle_detected or analysis.struggle_type is None:
        return ProcessRegime.PRODUCTIVE
    return ProcessRegime(analysis.struggle_type.value)


def is_bad(regime: ProcessRegime) -> bool:
    """Плохой режим = любое затруднение (не продуктивный)."""
    return regime != ProcessRegime.PRODUCTIVE


class DwellTracker:
    """Считает время непрерывного пребывания в одном режиме. Смена режима — сброс."""

    def __init__(self) -> None:
        self._regime: ProcessRegime | None = None
        self._since: datetime | None = None

    @property
    def current_regime(self) -> ProcessRegime | None:
        return self._regime

    def observe(self, regime: ProcessRegime, now: datetime) -> float:
        """Зафиксировать режим на момент now, вернуть dwell_seconds в текущем режиме."""
        if regime != self._regime:
            self._regime = regime
            self._since = now
            return 0.0
        return (now - self._since).total_seconds()
