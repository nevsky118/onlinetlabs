"""identify_regime — чистый анализ сессии в реальном времени, детекция struggle."""

from collections.abc import Callable

from agents.analytics.models import (
    AnalyticsResult,
    DifficultyLevel,
    DifficultyRecommendation,
    SessionFeatures,
    StruggleType,
    StudentMetrics,
    SuggestedIntervention,
)
from config.config_model import LearningAnalyticsConfig


# Правила детекции struggle
# (predicate, struggle_type, intervention, confidence_fn)

StruggleRule = tuple[
    Callable[[SessionFeatures, LearningAnalyticsConfig], bool],
    StruggleType,
    SuggestedIntervention,
    Callable[[SessionFeatures, LearningAnalyticsConfig], float],
]

STRUGGLE_RULES: list[StruggleRule] = [
    (
        lambda f, c: f.error_repeat_count >= c.error_repeat_threshold,
        StruggleType.REPEATING_ERRORS,
        SuggestedIntervention.HINT,
        lambda f, c: min(f.error_repeat_count / (c.error_repeat_threshold + 2), 1.0),
    ),
    # Прямой сигнал: много уникальных неверных ответов → trial-and-error (Table 1)
    (
        lambda f, c: f.distinct_failing_actuals > c.distinct_actuals_threshold,
        StruggleType.TRIAL_AND_ERROR,
        SuggestedIntervention.TUTOR,
        lambda f, c: min(f.distinct_failing_actuals / 4, 1.0),
    ),
    # Прямой сигнал: цикли без изменений → stuck (Table 1)
    (
        lambda f, c: f.cycles_failing_unchanged >= c.unchanged_cycles_threshold,
        StruggleType.STUCK_ON_STEP,
        SuggestedIntervention.HINT,
        lambda f, c: 0.7,
    ),
    (
        lambda f, c: (
            f.action_sequence_entropy > c.entropy_threshold
            and f.error_frequency > c.error_freq_threshold
        ),
        StruggleType.TRIAL_AND_ERROR,
        SuggestedIntervention.TUTOR,
        lambda f, c: min(f.action_sequence_entropy, 1.0),
    ),
    (
        lambda f, c: (
            f.idle_periods > c.idle_threshold and f.action_rate_slope < c.rate_slope_threshold
        ),
        StruggleType.IDLE,
        SuggestedIntervention.TUTOR,
        lambda f, c: 0.7,
    ),
    (
        lambda f, c: (
            f.time_on_current_step
            > c.stuck_time_multiplier * max(f.avg_inter_action_latency, c.min_latency_floor)
            and f.idle_periods > c.min_idle_for_stuck
        ),
        StruggleType.STUCK_ON_STEP,
        SuggestedIntervention.HINT,
        lambda f, c: 0.6,
    ),
]


def _detect_struggle(
    features: SessionFeatures, learning_analytics_config: LearningAnalyticsConfig
) -> tuple[StruggleType | None, SuggestedIntervention, float]:
    """Прогон правил; первое сработавшее побеждает."""
    for predicate, stype, interv, conf_fn in STRUGGLE_RULES:
        if predicate(features, learning_analytics_config):
            return stype, interv, conf_fn(features, learning_analytics_config)
    return None, SuggestedIntervention.NONE, 0.0


def identify_regime(
    features: SessionFeatures, config: LearningAnalyticsConfig
) -> AnalyticsResult:
    """Анализ сессии в реальном времени. Детекция struggle по правилам."""
    metrics = StudentMetrics(
        total_attempts=features.events_total,
        success_rate=1.0 - features.error_repeat_rate,
        avg_time_per_step=features.avg_inter_action_latency,
        struggling_steps=[],
    )
    diff_reco = DifficultyRecommendation(
        current_difficulty=DifficultyLevel.INTERMEDIATE.value,
        recommended_difficulty=DifficultyLevel.INTERMEDIATE.value,
        reasoning="Анализ на основе сессии",
        metrics=metrics,
    )

    struggle_type, intervention, confidence = _detect_struggle(features, config)

    return AnalyticsResult(
        difficulty_recommendation=diff_reco,
        struggle_detected=struggle_type is not None,
        struggle_type=struggle_type,
        suggested_intervention=intervention,
        features=features,
        confidence=confidence,
    )
