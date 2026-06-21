"""Размеченные сценарии для оценки идентификатора П1 (синтетика + загруженные реальные)."""
from dataclasses import dataclass
from datetime import datetime, timezone

from agents.analytics.models import SessionFeatures
from learning_analytics.process_state import ProcessRegime

# Фиксированный момент времени для синтетических снапшотов (computed_at — обязательное поле)
_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


@dataclass
class Snapshot:
    ts: float                  # секунды от старта сессии
    features: SessionFeatures


@dataclass
class LabeledScenario:
    snapshots: list["Snapshot"]
    onset_ts: float | None     # None ⟺ нормальная сессия
    onset_window: float        # ±Δ допуск (сек)
    truth_regime: ProcessRegime
    duration_seconds: float
    source: str                # "synthetic" | "real"


def is_normal(s: "LabeledScenario") -> bool:
    return s.truth_regime == ProcessRegime.PRODUCTIVE


def _features(ts_index: int, regime: ProcessRegime, fired: bool) -> SessionFeatures:
    """Benign-фичи; если fired — пробивают правило для regime (дефолтные пороги конфига)."""
    # Адаптация: SessionFeatures требует computed_at (datetime); user_id/lab_slug отсутствуют в модели
    base = dict(
        avg_inter_action_latency=5.0,
        action_rate_slope=0.0,
        idle_periods=0,
        total_active_time=10.0,
        time_on_current_step=10.0,
        error_repeat_count=0,
        error_repeat_rate=0.0,
        action_sequence_entropy=0.0,
        undo_redo_ratio=0.0,
        error_frequency=0.0,
        error_frequency_slope=0.0,
        unique_error_types=0,
        dominant_error=None,
        components_touched=1,
        action_diversity=0.5,
        events_total=ts_index + 1,
        distinct_failing_actuals=0,
        cycles_failing_unchanged=0,
        session_id="syn",
        computed_at=_EPOCH,
    )
    if fired:
        if regime == ProcessRegime.REPEATING_ERRORS:
            base.update(error_repeat_count=5, error_repeat_rate=0.6, error_frequency=0.6)
        elif regime == ProcessRegime.TRIAL_AND_ERROR:
            base.update(distinct_failing_actuals=5, action_sequence_entropy=0.9, error_frequency=0.6)
        elif regime == ProcessRegime.STUCK_ON_STEP:
            base.update(cycles_failing_unchanged=4)
        elif regime == ProcessRegime.IDLE:
            base.update(idle_periods=4, avg_inter_action_latency=120.0)
    return SessionFeatures(**base)


def make_normal_scenario(n: int = 12, step: float = 15.0, source: str = "synthetic") -> "LabeledScenario":
    snaps = [Snapshot(i * step, _features(i, ProcessRegime.PRODUCTIVE, False)) for i in range(n)]
    return LabeledScenario(snaps, None, 0.0, ProcessRegime.PRODUCTIVE, n * step, source)


def make_struggle_scenario(
    regime: ProcessRegime,
    onset_index: int = 6,
    n: int = 12,
    step: float = 15.0,
    window: float = 30.0,
    source: str = "synthetic",
) -> "LabeledScenario":
    snaps = [Snapshot(i * step, _features(i, regime, fired=(i >= onset_index))) for i in range(n)]
    return LabeledScenario(snaps, onset_index * step, window, regime, n * step, source)
