"""Pydantic-схемы для experiment API."""

from datetime import datetime

from pydantic import BaseModel


class ExperimentStatusResponse(BaseModel):
    """Статус эксперимента."""
    total_participants: int
    control_count: int
    experimental_count: int
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
