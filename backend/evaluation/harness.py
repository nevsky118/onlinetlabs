"""Прогон идентификатора П1 (полный конвейер feature→rule→dwell) по сценарию при пороге T_k."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from agents.analytics.agent import AnalyticsAgent
from agents.analytics.models import (
    AnalyticsResult,
    DifficultyLevel,
    DifficultyRecommendation,
    StudentMetrics,
)
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


def _analyze(features, config: LearningAnalyticsConfig) -> AnalyticsResult:
    """Полный конвейер анализа без инстанцирования BaseAgent (нет ConfigModel)."""
    struggle_type, intervention, confidence = AnalyticsAgent._detect_struggle(features, config)
    metrics = StudentMetrics(
        total_attempts=features.events_total,
        success_rate=1.0 - features.error_repeat_rate,
        avg_time_per_step=features.avg_inter_action_latency,
        struggling_steps=[],
    )
    diff_reco = DifficultyRecommendation(
        current_difficulty=DifficultyLevel.INTERMEDIATE.value,
        recommended_difficulty=DifficultyLevel.INTERMEDIATE.value,
        reasoning="eval",
        metrics=metrics,
    )
    return AnalyticsResult(
        difficulty_recommendation=diff_reco,
        struggle_detected=struggle_type is not None,
        struggle_type=struggle_type,
        suggested_intervention=intervention,  # _detect_struggle всегда даёт NONE при отсутствии
        features=features,
        confidence=confidence,
    )


def run_identifier(
    scenario: LabeledScenario, t_k: float, config: LearningAnalyticsConfig
) -> Detection:
    """Прогоняет полный конвейер по снапшотам сценария при пороге dwell T_k."""
    tracker = DwellTracker()
    for snap in scenario.snapshots:
        result = _analyze(snap.features, config)
        regime = analysis_to_regime(result)
        dwell = tracker.observe(regime, _BASE + timedelta(seconds=snap.ts))
        if is_bad(regime) and dwell >= t_k:
            return Detection(True, snap.ts, regime)
    return Detection(False, None, None)
