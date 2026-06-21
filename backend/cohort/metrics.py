"""Когортные орг-метрики D3/D4. Чистое ядро (без БД): KM с цензурированием + агрегаторы."""
from dataclasses import dataclass


@dataclass
class LearnerOutcome:
    user_id: str
    skill: str
    arm: str | None
    reached_l2: bool
    time_to_l2_seconds: float | None
    active_seconds: float | None
    sessions_to_l2: int | None
    l1_interventions: int
    l2_interventions: int | None
    l1_escalations: int
    l2_escalations: int | None
    l1_repeated_errors: int
    l2_repeated_errors: int | None
    observation_seconds: float
    censored: bool


@dataclass
class TimeToCompetence:
    median_calendar_seconds: float | None
    median_active_seconds: float | None
    reach_rate: float
    reach_rate_at_horizon: float
    restricted_mean_calendar_seconds: float
    n: int
    censored: int


@dataclass
class AutonomyMetrics:
    mean_l1_interventions: float
    mean_l2_interventions: float | None
    mean_sessions_to_l2: float | None


def _survival_steps(durations: list[float], events: list[bool]) -> list[tuple[float, float]]:
    """Точки кривой выживания KM: [(t, S(t))...] по возрастанию t. S падает только на событиях."""
    if not durations:
        return []
    paired = sorted(zip(durations, events), key=lambda x: x[0])
    n_at_risk = len(paired)
    surv = 1.0
    steps: list[tuple[float, float]] = []
    i = 0
    times = sorted({t for t, _ in paired})
    for t in times:
        d_i = sum(1 for tt, ev in paired if tt == t and ev)   # события в момент t
        c_i = sum(1 for tt, ev in paired if tt == t)          # все выбывшие (события + цензур)
        if n_at_risk > 0 and d_i > 0:
            surv *= 1.0 - d_i / n_at_risk
        steps.append((t, surv))
        n_at_risk -= c_i
    return steps


def kaplan_meier_median(
    durations: list[float], events: list[bool], reach_rate: float | None = None
) -> float | None:
    """Медиана = первый t с S(t) < 0.5. None, если <50% дошли (разрежённая страта).
    reach_rate — авторитетная доля дошедших по полной популяции; иначе sum(events)/len."""
    if not events:
        return None
    r = reach_rate if reach_rate is not None else sum(events) / len(events)
    if r < 0.5:
        return None
    for t, s in _survival_steps(durations, events):
        if s < 0.5:
            return t
    return None


def reach_rate_at(durations: list[float], events: list[bool], horizon: float) -> float:
    """Доля достигших события к horizon = 1 - S(horizon)."""
    steps = _survival_steps(durations, events)
    if not steps:
        return 0.0
    surv = 1.0
    for t, s in steps:
        if t <= horizon:
            surv = s
        else:
            break
    return 1.0 - surv


def restricted_mean(durations: list[float], events: list[bool], horizon: float) -> float:
    """RMST = площадь под S(t) на [0, horizon] (трапеции по ступеням)."""
    steps = _survival_steps(durations, events)
    if not steps:
        return 0.0
    area = 0.0
    prev_t, prev_s = 0.0, 1.0
    for t, s in steps:
        seg_t = min(t, horizon)
        area += prev_s * (seg_t - prev_t)   # S ступенчата: до t держится prev_s
        prev_t, prev_s = seg_t, s
        if t >= horizon:
            return area
    area += prev_s * (horizon - prev_t)     # хвост до горизонта
    return area


def _durations_events(records: list["LearnerOutcome"], active: bool) -> tuple[list[float], list[bool]]:
    """(durations, events) для KM: достигшие → time_to_l2/active + event=True; цензур → observation + False."""
    durations, events = [], []
    for r in records:
        if r.reached_l2:
            val = r.active_seconds if active else r.time_to_l2_seconds
            if val is None:
                continue
            durations.append(val)
            events.append(True)
        else:
            durations.append(r.observation_seconds)
            events.append(False)
    return durations, events


def time_to_competence(records: list["LearnerOutcome"], horizon_seconds: float) -> "TimeToCompetence":
    n = len(records)
    censored = sum(1 for r in records if not r.reached_l2)
    cal_d, cal_e = _durations_events(records, active=False)
    act_d, act_e = _durations_events(records, active=True)
    reached = sum(1 for r in records if r.reached_l2)
    reach = (reached / n) if n else 0.0
    return TimeToCompetence(
        # авторитетная доля reach (по полной популяции) → решение о фолбэке медианы
        median_calendar_seconds=kaplan_meier_median(cal_d, cal_e, reach_rate=reach),
        median_active_seconds=kaplan_meier_median(act_d, act_e, reach_rate=reach),
        reach_rate=reach,
        reach_rate_at_horizon=reach_rate_at(cal_d, cal_e, horizon_seconds),
        restricted_mean_calendar_seconds=restricted_mean(cal_d, cal_e, horizon_seconds),
        n=n,
        censored=censored,
    )


def _mean(vals: list[float]) -> float | None:
    return sum(vals) / len(vals) if vals else None


def autonomy_metrics(records: list["LearnerOutcome"]) -> "AutonomyMetrics":
    l2_recs = [r for r in records if r.reached_l2]
    return AutonomyMetrics(
        mean_l1_interventions=_mean([float(r.l1_interventions) for r in records]) or 0.0,
        mean_l2_interventions=_mean([float(r.l2_interventions) for r in l2_recs if r.l2_interventions is not None]),
        mean_sessions_to_l2=_mean([float(r.sessions_to_l2) for r in l2_recs if r.sessions_to_l2 is not None]),
    )


# Task 4: D4 описательный тренд L1→L2 + survivorship-пометка
SURVIVORSHIP_NOTE = (
    "Описательный/разведочный тренд: считается по дошедшим до L2 (= успешные), "
    "возможен survivorship bias + регрессия к среднему. НЕ доказательство снижения "
    "платформой. Каузальное снижение — Задача 4 (open vs closed)."
)


@dataclass
class OrgEffectTrend:
    l1_escalations_mean: float
    l2_escalations_mean: float | None
    l1_repeated_errors_mean: float
    l2_repeated_errors_mean: float | None
    note: str


def org_effect_trend(records: list["LearnerOutcome"]) -> "OrgEffectTrend":
    l2_recs = [r for r in records if r.reached_l2]
    return OrgEffectTrend(
        l1_escalations_mean=_mean([float(r.l1_escalations) for r in records]) or 0.0,
        l2_escalations_mean=_mean([float(r.l2_escalations) for r in l2_recs if r.l2_escalations is not None]),
        l1_repeated_errors_mean=_mean([float(r.l1_repeated_errors) for r in records]) or 0.0,
        l2_repeated_errors_mean=_mean([float(r.l2_repeated_errors) for r in l2_recs if r.l2_repeated_errors is not None]),
        note=SURVIVORSHIP_NOTE,
    )


# Task 5: агрегация по стратам (skill + опц. arm) + pooled + headline=closed
@dataclass
class CohortCell:
    skill: str | None
    arm: str | None
    n: int
    time_to_competence: "TimeToCompetence"
    autonomy: "AutonomyMetrics"
    org_effect: "OrgEffectTrend"


def _cell(records: list["LearnerOutcome"], horizon: float, skill: str | None, arm: str | None) -> "CohortCell":
    return CohortCell(
        skill=skill, arm=arm, n=len(records),
        time_to_competence=time_to_competence(records, horizon),
        autonomy=autonomy_metrics(records),
        org_effect=org_effect_trend(records),
    )


def aggregate_cohort(records: list["LearnerOutcome"], horizon_seconds: float, by_arm: bool = False) -> dict:
    by_skill: list[CohortCell] = []
    for skill in sorted({r.skill for r in records}):
        by_skill.append(_cell([r for r in records if r.skill == skill], horizon_seconds, skill, None))
    by_arm_cells = None
    if by_arm:
        by_arm_cells = []
        for arm in sorted({r.arm for r in records if r.arm}):
            by_arm_cells.append(_cell([r for r in records if r.arm == arm], horizon_seconds, None, arm))
    return {
        "by_skill": by_skill,
        "pooled": _cell(records, horizon_seconds, None, None),
        "by_arm": by_arm_cells,
        "headline_arm": "closed",
    }


# Task 6: retention-метрика (year-1 помечена смещённой)
RETENTION_NOTE = (
    "Оппортунистический/смещённый/предварительный показатель: самоселекция "
    "(ретестятся мотивированные) → крошечная смещённая выборка. НЕ результат. "
    "Реальный retention — спланированный ретест 2-го года."
)


@dataclass
class RetentionMetric:
    retest_count: int
    retest_pass_rate: float | None
    note: str


def retention_metric(retests: list[bool]) -> "RetentionMetric":
    n = len(retests)
    return RetentionMetric(
        retest_count=n,
        retest_pass_rate=(sum(1 for x in retests if x) / n) if n else None,
        note=RETENTION_NOTE,
    )
