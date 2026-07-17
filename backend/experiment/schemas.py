"""Pydantic schemas for the experiment API."""

from datetime import datetime

from pydantic import BaseModel


class ArmAnalysisResponse(BaseModel):
    """Result of comparing the open vs closed arm."""

    l2_pass_rate_open: float
    l2_pass_rate_closed: float
    escalations_mean_open: float
    escalations_mean_closed: float
    repeated_errors_comparison: dict
    mentor_hours_saved: float


class ExperimentStatusResponse(BaseModel):
    """Experiment status."""

    total_participants: int
    group_a_count: int
    group_b_count: int
    completed_count: int
    in_progress_count: int


class ParticipantResponse(BaseModel):
    """Experiment participant."""

    user_id: str
    email: str | None
    name: str | None
    experiment_group: str | None
    sessions_count: int
    completed: bool
    total_time_seconds: float | None


class GroupUpdateRequest(BaseModel):
    """Request to change group."""

    group: str


class TimelineEventResponse(BaseModel):
    """Event in the session timeline."""

    timestamp: datetime
    event_type: str
    action: str
    component_id: str | None
    message: str | None
    success: bool
