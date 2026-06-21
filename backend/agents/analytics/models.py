"""Модели AnalyticsAgent."""

from enum import Enum
from datetime import datetime
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


class DifficultyLevel(str, Enum):
    """Уровни сложности."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class StruggleType(str, Enum):
    """Типы затруднений студента: застрял на шаге, повтор ошибок, простой, метод проб и ошибок."""
    STUCK_ON_STEP = "stuck_on_step"
    REPEATING_ERRORS = "repeating_errors"
    IDLE = "idle"
    TRIAL_AND_ERROR = "trial_and_error"


class SuggestedIntervention(str, Enum):
    """Рекомендуемые интервенции: подсказка, тьютор, упрощение или ничего."""
    HINT = "hint"
    TUTOR = "tutor"
    SIMPLIFY = "simplify"
    NONE = "none"


class SessionFeatures(BaseModel):
    """Вычисленные фичи сессии на момент времени."""
    # Темпоральные
    avg_inter_action_latency: float
    action_rate_slope: float
    idle_periods: int
    total_active_time: float
    time_on_current_step: float
    # Последовательные
    error_repeat_count: int
    error_repeat_rate: float
    action_sequence_entropy: float
    undo_redo_ratio: float
    # Ошибки
    error_frequency: float
    error_frequency_slope: float
    unique_error_types: int
    dominant_error: str | None
    # Прогресс
    components_touched: int
    action_diversity: float
    events_total: int
    # Признаки spec-проверок
    distinct_failing_actuals: int = 0
    cycles_failing_unchanged: int = 0
    # Мета
    session_id: str
    computed_at: datetime


class AnalyticsResult(BaseModel):
    """Результат аналитики сессии в реальном времени."""
    difficulty_recommendation: DifficultyRecommendation
    struggle_detected: bool
    struggle_type: StruggleType | None = None
    suggested_intervention: SuggestedIntervention = SuggestedIntervention.NONE
    features: SessionFeatures
    confidence: float = Field(ge=0.0, le=1.0)
