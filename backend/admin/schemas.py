"""Схемы ответов admin-эндпоинтов."""
from pydantic import BaseModel


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
