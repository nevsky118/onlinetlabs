"""AnalyticsAgent — анализ прогресса и адаптация сложности."""

from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from config.config_model import ConfigModel, LearningAnalyticsConfig
from agents.base import BaseAgent
from agents.analytics.models import (
    AnalyticsInput,
    AnalyticsResult,
    DifficultyRecommendation,
    SessionFeatures,
    StudentMetrics,
    StruggleType,
    SuggestedIntervention,
)
from agents.analytics.tools import AnalyticsTools


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
            f.idle_periods > c.idle_threshold
            and f.action_rate_slope < c.rate_slope_threshold
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


class AnalyticsAgent(BaseAgent):
    """Анализ поведения студента, рекомендация сложности и детекция struggle."""

    def __init__(self, config: ConfigModel, db: AsyncSession | None):
        self.tools = AnalyticsTools(db)
        super().__init__(config)

    def system_prompt(self) -> str:
        """Системный промпт агента."""
        return (
            "Ты — AnalyticsAgent, агент для анализа поведения студента. "
            "Твоя роль: вычислять метрики прогресса, находить паттерны ошибок, "
            "рекомендовать уровень сложности. Будь объективен."
        )

    async def run(self, input_data: AnalyticsInput) -> DifficultyRecommendation:
        """Получить попытки из DB, вычислить метрики, рекомендовать сложность."""
        attempts = await self.tools.get_attempts(
            input_data.user_id, input_data.lab_slug
        )
        return self.analyze(attempts, current_difficulty="intermediate")

    def analyze(
        self, attempts: list, current_difficulty: str
    ) -> DifficultyRecommendation:
        """Пакетный анализ по StepAttempt. Рекомендация сложности."""
        metrics = self.tools.compute_metrics(attempts)
        error_patterns = self.tools.detect_error_patterns(attempts)

        if metrics.success_rate >= 0.9:
            recommended = "advanced"
            reasoning = "Высокий процент успеха — можно увеличить сложность."
        elif metrics.success_rate <= 0.3 or len(metrics.struggling_steps) > 0:
            recommended = "beginner"
            reasoning = "Низкий процент успеха или проблемные шаги — снизить сложность."
        else:
            recommended = current_difficulty
            reasoning = "Средний прогресс — сохранить текущий уровень."

        return DifficultyRecommendation(
            current_difficulty=current_difficulty,
            recommended_difficulty=recommended,
            reasoning=reasoning,
            metrics=metrics,
            error_patterns=error_patterns,
        )

    def analyze_session(
        self, features: SessionFeatures, learning_analytics_config: LearningAnalyticsConfig
    ) -> AnalyticsResult:
        """Анализ сессии в реальном времени. Детекция struggle по правилам."""
        metrics = StudentMetrics(
            total_attempts=features.events_total,
            success_rate=1.0 - features.error_repeat_rate,
            avg_time_per_step=features.avg_inter_action_latency,
            struggling_steps=[],
        )
        diff_reco = DifficultyRecommendation(
            current_difficulty="intermediate",
            recommended_difficulty="intermediate",
            reasoning="Анализ на основе сессии",
            metrics=metrics,
        )

        struggle_type, intervention, confidence = self._detect_struggle(
            features, learning_analytics_config
        )

        return AnalyticsResult(
            difficulty_recommendation=diff_reco,
            struggle_detected=struggle_type is not None,
            struggle_type=struggle_type,
            suggested_intervention=intervention,
            features=features,
            confidence=confidence,
        )

    @staticmethod
    def _detect_struggle(
        features: SessionFeatures, learning_analytics_config: LearningAnalyticsConfig
    ) -> tuple[StruggleType | None, SuggestedIntervention, float]:
        """Прогон правил; первое сработавшее побеждает."""
        for predicate, stype, interv, conf_fn in STRUGGLE_RULES:
            if predicate(features, learning_analytics_config):
                return stype, interv, conf_fn(features, learning_analytics_config)
        return None, SuggestedIntervention.NONE, 0.0
