"""Модели AnalyticsAgent."""

from pydantic import BaseModel, Field


class StudentMetrics(BaseModel):
    """Метрики студента по лабе."""

    total_attempts: int
    success_rate: float = Field(ge=0.0, le=1.0)
    avg_time_per_step: float = Field(description="Среднее время на шаг (секунды)")
    struggling_steps: list[str] = Field(description="Шаги с >2 неудачами подряд")


class AnalyticsInput(BaseModel):
    """Вход для аналитики."""

    user_id: str
    lab_slug: str


class DifficultyRecommendation(BaseModel):
    """Рекомендация по сложности."""

    current_difficulty: str
    recommended_difficulty: str
    reasoning: str
    metrics: StudentMetrics
    error_patterns: list[str] = Field(default_factory=list)
