"""Pydantic-схемы для API эксперимента."""

from datetime import datetime

from pydantic import BaseModel


class ArmAnalysisResponse(BaseModel):
    """Результат сравнения open vs closed arm."""

    l2_pass_rate_open: float
    l2_pass_rate_closed: float
    escalations_mean_open: float
    escalations_mean_closed: float
    repeated_errors_comparison: dict
    mentor_hours_saved: float


class ExperimentStatusResponse(BaseModel):
    """Статус эксперимента."""

    total_participants: int
    group_a_count: int
    group_b_count: int
    completed_count: int
    in_progress_count: int


class ParticipantResponse(BaseModel):
    """Участник эксперимента."""

    user_id: str
    email: str | None
    name: str | None
    experiment_group: str | None
    sessions_count: int
    completed: bool
    total_time_seconds: float | None


class GroupUpdateRequest(BaseModel):
    """Запрос на смену группы."""

    group: str


class TimelineEventResponse(BaseModel):
    """Событие в таймлайне сессии."""

    timestamp: datetime
    event_type: str
    action: str
    component_id: str | None
    message: str | None
    success: bool
