import dataclasses
from datetime import datetime

from pydantic import BaseModel


class MCPAuditRow(BaseModel):
    """Одна запись аудита MCP-вызовов через контур."""

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
    """Сессия ученика для списка в карточке преподавателя."""

    session_id: str
    lab_slug: str
    lab_title: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    message_count: int
    hint_count: int


class StudentOverview(BaseModel):
    """Сводка по одному ученику для общей таблицы кабинета преподавателя."""

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
    """Список учеников со сводной статистикой и агрегатами по группе."""

    students: list[StudentOverview]
    total_students: int
    total_hints: int


class LabProgressRow(BaseModel):
    """Прогресс ученика по одной лабе с числом подсказок и попыток."""

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
    """Детальная карточка ученика: профиль и прогресс по всем лабам."""

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
    """Элемент таймлайна сессии: реплика чата или проактивная интервенция."""

    kind: str  # student | tutor | intervention
    ts: datetime
    parts: list | None = None
    text: str | None = None
    action: str | None = None
    severity: str | None = None
    hint_level: int | None = None
    struggle_type: str | None = None


# --- Когортные орг-метрики Task 8 ---


class TimeToCompetenceSchema(BaseModel):
    """Зеркало dataclass TimeToCompetence."""

    median_calendar_seconds: float | None
    median_active_seconds: float | None
    reach_rate: float
    reach_rate_at_horizon: float
    restricted_mean_calendar_seconds: float
    n: int
    censored: int


class AutonomySchema(BaseModel):
    """Зеркало dataclass AutonomyMetrics."""

    mean_l1_interventions: float
    mean_l2_interventions: float | None
    mean_sessions_to_l2: float | None


class OrgEffectSchema(BaseModel):
    """Зеркало dataclass OrgEffectTrend; note-строка передаётся как есть."""

    l1_escalations_mean: float
    l2_escalations_mean: float | None
    l1_repeated_errors_mean: float
    l2_repeated_errors_mean: float | None
    note: str


class CohortCellSchema(BaseModel):
    """Зеркало dataclass CohortCell."""

    skill: str | None
    arm: str | None
    n: int
    time_to_competence: TimeToCompetenceSchema
    autonomy: AutonomySchema
    org_effect: OrgEffectSchema


class CohortMetricsResponse(BaseModel):
    """Ответ GET /instructor/cohort-metrics."""

    by_skill: list[CohortCellSchema]
    pooled: CohortCellSchema
    by_arm: list[CohortCellSchema] | None
    headline_arm: str


def _cell_schema(cell) -> CohortCellSchema:
    """Конвертирует CohortCell dataclass → CohortCellSchema."""
    d = dataclasses.asdict(cell)
    return CohortCellSchema(
        skill=d["skill"],
        arm=d["arm"],
        n=d["n"],
        time_to_competence=TimeToCompetenceSchema(**d["time_to_competence"]),
        autonomy=AutonomySchema(**d["autonomy"]),
        org_effect=OrgEffectSchema(**d["org_effect"]),
    )


def cohort_response_from_result(out: dict) -> CohortMetricsResponse:
    """Маппит результат aggregate_cohort → CohortMetricsResponse."""
    return CohortMetricsResponse(
        by_skill=[_cell_schema(c) for c in out["by_skill"]],
        pooled=_cell_schema(out["pooled"]),
        by_arm=[_cell_schema(c) for c in out["by_arm"]] if out["by_arm"] is not None else None,
        headline_arm=out["headline_arm"],
    )
