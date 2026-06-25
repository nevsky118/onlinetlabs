"""Схемы ответов admin-эндпоинтов."""
from pydantic import BaseModel

from models.user import UserRole


class OverviewAb(BaseModel):
    l2_pass_closed: float
    l2_pass_open: float
    mentor_hours_saved: float


class OverviewCohort(BaseModel):
    pooled_reach_rate: float
    pooled_n: int


class OverviewIdentifier(BaseModel):
    j_optimal_t_k: float
    recall_at_opt: float
    costs: dict


class OverviewOps(BaseModel):
    active_sessions: int
    total_interventions: int
    labeled_real_n: int


class OverviewResponse(BaseModel):
    ab: OverviewAb
    cohort: OverviewCohort
    identifier: OverviewIdentifier
    ops: OverviewOps


class CurvePoint(BaseModel):
    t_k: float
    latency_median: float | None
    false_per_hour: float
    recall: float
    j: float


class IdentifierEvalResponse(BaseModel):
    curve: list[CurvePoint]
    j_optimal_t_k: float
    confusion: dict
    first_match: dict
    costs: dict
    preliminary: bool


class TkPoint(BaseModel):
    ratio: float
    t_k: float
    J: float


class TkSensitivityResponse(BaseModel):
    points: list[TkPoint]
    costs: dict[str, float]


class UserListItem(BaseModel):
    id: str
    name: str | None
    email: str | None
    image: str | None
    role: str
    can_select_model: bool | None
    can_view_agent_logs: bool | None


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int
    page: int
    page_size: int


class UserUpdate(BaseModel):
    role: UserRole | None = None
    can_select_model: bool | None = None
    can_view_agent_logs: bool | None = None


class AdminLab(BaseModel):
    slug: str
    title: str
    enabled: bool
    environment_type: str
    course_slug: str | None
    gns3_template_project_id: str | None
    gns3_template_project_id_frr: str | None
    gns3_template_project_id_iosvl2: str | None
    template_ready: bool
    template_status: str


class AdminLabUpdate(BaseModel):
    enabled: bool | None = None
    gns3_template_project_id: str | None = None
    gns3_template_project_id_frr: str | None = None
    gns3_template_project_id_iosvl2: str | None = None


class AdminDataResponse(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int
    columns: list[str]
    sortable: list[str]
