from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class TimeToCompetenceSchema(BaseModel):
    """Mirror of the TimeToCompetence dataclass."""

    model_config = ConfigDict(from_attributes=True)

    median_calendar_seconds: float | None
    median_active_seconds: float | None
    reach_rate: float
    reach_rate_at_horizon: float
    restricted_mean_calendar_seconds: float
    n: int
    censored: int


class AutonomySchema(BaseModel):
    """Mirror of the AutonomyMetrics dataclass."""

    model_config = ConfigDict(from_attributes=True)

    mean_l1_interventions: float
    mean_l2_interventions: float | None
    mean_sessions_to_l2: float | None


class OrgEffectSchema(BaseModel):
    """Mirror of the OrgEffectTrend dataclass; the note string passes through as-is."""

    model_config = ConfigDict(from_attributes=True)

    l1_escalations_mean: float
    l2_escalations_mean: float | None
    l1_repeated_errors_mean: float
    l2_repeated_errors_mean: float | None
    note: str


class CohortCellSchema(BaseModel):
    """Mirror of the CohortCell dataclass."""

    model_config = ConfigDict(from_attributes=True)

    skill: str | None
    arm: str | None
    n: int
    time_to_competence: TimeToCompetenceSchema
    autonomy: AutonomySchema
    org_effect: OrgEffectSchema


class CohortMetricsResponse(BaseModel):
    """Response for GET /instructor/cohort-metrics."""

    by_skill: list[CohortCellSchema]
    pooled: CohortCellSchema
    by_arm: list[CohortCellSchema] | None
    headline_arm: str


def _cell_schema(cell) -> CohortCellSchema:
    """Converts a CohortCell dataclass to CohortCellSchema."""
    return CohortCellSchema.model_validate(cell)


def cohort_response_from_result(out: dict) -> CohortMetricsResponse:
    """Maps the aggregate_cohort result to CohortMetricsResponse."""
    return CohortMetricsResponse(
        by_skill=[_cell_schema(c) for c in out["by_skill"]],
        pooled=_cell_schema(out["pooled"]),
        by_arm=[_cell_schema(c) for c in out["by_arm"]] if out["by_arm"] is not None else None,
        headline_arm=out["headline_arm"],
    )
