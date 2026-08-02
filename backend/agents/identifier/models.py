"""Models for identify_regime and batch progress analytics."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class StudentMetrics(BaseModel):
    """Student metrics for a lab."""

    total_attempts: int
    success_rate: float = Field(ge=0.0, le=1.0)
    avg_time_per_step: float = Field(description="Среднее время на шаг (секунды)")
    struggling_steps: list[str] = Field(description="Шаги с >2 неудачами подряд")


class DifficultyRecommendation(BaseModel):
    """Difficulty recommendation."""

    current_difficulty: str
    recommended_difficulty: str
    reasoning: str
    metrics: StudentMetrics
    error_patterns: list[str] = Field(default_factory=list)


class DifficultyLevel(str, Enum):
    """Difficulty levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class StruggleType(str, Enum):
    """Types of student struggle (stuck on step, repeating errors, idle, trial and error)."""

    STUCK_ON_STEP = "stuck_on_step"
    REPEATING_ERRORS = "repeating_errors"
    IDLE = "idle"
    TRIAL_AND_ERROR = "trial_and_error"


class SuggestedIntervention(str, Enum):
    """Suggested intervention (hint, tutor, simplify, or none)."""

    HINT = "hint"
    TUTOR = "tutor"
    SIMPLIFY = "simplify"
    NONE = "none"


class SessionFeatures(BaseModel):
    """Computed session features at a point in time."""

    # Temporal
    avg_inter_action_latency: float
    action_rate_slope: float
    idle_periods: int
    total_active_time: float
    time_on_current_step: float
    # Sequential
    error_repeat_count: int
    error_repeat_rate: float
    action_sequence_entropy: float
    undo_redo_ratio: float
    # Errors
    error_frequency: float
    error_frequency_slope: float
    unique_error_types: int
    dominant_error: str | None
    # Progress
    components_touched: int
    action_diversity: float
    events_total: int
    # Spec-check features
    distinct_failing_actuals: int = 0
    cycles_failing_unchanged: int = 0
    # Meta
    session_id: str
    computed_at: datetime


class AnalyticsResult(BaseModel):
    """Real-time session analytics result."""

    difficulty_recommendation: DifficultyRecommendation
    struggle_detected: bool
    struggle_type: StruggleType | None = None
    suggested_intervention: SuggestedIntervention = SuggestedIntervention.NONE
    features: SessionFeatures
    confidence: float = Field(ge=0.0, le=1.0)
