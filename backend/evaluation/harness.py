"""Прогон идентификатора П1 (полный конвейер feature→rule→dwell) по сценарию при пороге T_k."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from agents.analytics.agent import identify_regime
from config.config_model import LearningAnalyticsConfig
from evaluation.scenarios import LabeledScenario
from learning_analytics.process_state import DwellTracker, ProcessRegime, analysis_to_regime, is_bad

# Фикс. база для перевода snap.ts (float, сек) → datetime
_BASE = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass
class Detection:
    detected: bool
    detected_ts: float | None
    detected_regime: ProcessRegime | None


def run_identifier(
    scenario: LabeledScenario, t_k: float, config: LearningAnalyticsConfig
) -> Detection:
    """Прогоняет полный конвейер по снапшотам сценария при пороге dwell T_k."""
    tracker = DwellTracker()
    for snap in scenario.snapshots:
        result = identify_regime(snap.features, config)
        regime = analysis_to_regime(result)
        dwell = tracker.observe(regime, _BASE + timedelta(seconds=snap.ts))
        if is_bad(regime) and dwell >= t_k:
            return Detection(True, snap.ts, regime)
    return Detection(False, None, None)
