"""AnalyticsAgent — анализ прогресса и адаптация сложности."""

from sqlalchemy.ext.asyncio import AsyncSession

from config.config_model import ConfigModel
from agents.base import BaseAgent
from agents.analytics.models import (
    AnalyticsInput,
    DifficultyRecommendation,
)
from agents.analytics.tools import AnalyticsTools


class AnalyticsAgent(BaseAgent):
    """Агент для анализа прогресса студента и рекомендации сложности."""

    def __init__(self, config: ConfigModel, db: AsyncSession | None):
        self.tools = AnalyticsTools(db)
        super().__init__(config)

    def system_prompt(self) -> str:
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
        """Вычислить метрики и рекомендовать сложность (без DB вызовов)."""
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
