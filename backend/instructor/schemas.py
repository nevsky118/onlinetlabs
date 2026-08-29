from datetime import datetime

from pydantic import BaseModel

from analytics.cohort.metrics import CohortCell


class MCPAuditRow(BaseModel):
    """A single audit record of MCP calls through the control loop."""

    id: str
    user_id: str
    session_id: str
    tool: str
    kind: str
    ts: datetime
    success: bool
    error: str | None
    consent_ref: str | None
    lab_slug: str | None

    model_config = {"from_attributes": True}


class SessionSummary(BaseModel):
    """A student session for the list in the instructor dashboard."""

    session_id: str
    lab_slug: str
    lab_title: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    message_count: int
    hint_count: int


class StudentOverview(BaseModel):
    """Overview of one student for the instructor dashboard's overview table."""

    user_id: str
    name: str | None
    email: str | None
    labs_total: int
    labs_completed: int
    labs_in_progress: int
    avg_score: float | None
    total_hints: int
    total_sessions: int
    last_active_at: datetime | None


class StudentsOverviewResponse(BaseModel):
    """List of students with summary stats and group-level aggregates."""

    students: list[StudentOverview]
    total_students: int
    total_hints: int


class LabProgressRow(BaseModel):
    """Student's progress on one lab with hint and attempt counts."""

    lab_slug: str
    lab_title: str
    status: str
    score: float | None
    current_step: int | None
    hints: int
    sessions: int
    attempts: int
    started_at: datetime | None
    completed_at: datetime | None
    last_active_at: datetime | None


class StudentDetailResponse(BaseModel):
    """Detailed student card: profile and progress across all labs."""

    user_id: str
    name: str | None
    email: str | None
    role: str
    labs_completed: int
    labs_in_progress: int
    avg_score: float | None
    total_hints: int
    total_sessions: int
    labs: list[LabProgressRow]
    sessions: list[SessionSummary]


class TimelineItem(BaseModel):
    """A session timeline item: a chat message or a proactive intervention."""

    kind: str  # student | tutor | intervention
    ts: datetime
    parts: list | None = None
    text: str | None = None
    action: str | None = None
    severity: str | None = None
    hint_level: int | None = None
    struggle_type: str | None = None


# --- Cohort org metrics Task 8 ---
# The domain types are pydantic models, so the response composes them directly.


class CohortMetricsResponse(BaseModel):
    """Response for GET /instructor/cohort-metrics."""

    by_skill: list[CohortCell]
    pooled: CohortCell
    by_arm: list[CohortCell] | None
    headline_arm: str


def cohort_response_from_result(out: dict) -> CohortMetricsResponse:
    """Maps the aggregate_cohort result to CohortMetricsResponse."""
    return CohortMetricsResponse(**out)
