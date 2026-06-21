"""Admin-роутер: /admin/overview, /admin/identifier-eval, /admin/tk-sensitivity."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.schemas import (
    CurvePoint,
    IdentifierEvalResponse,
    OverviewAb,
    OverviewCohort,
    OverviewIdentifier,
    OverviewOps,
    OverviewResponse,
    TkPoint,
    TkSensitivityResponse,
)
from auth.dependencies import get_current_user
from config.config_model import LearningAnalyticsConfig
from control.criterion import Costs
from control.derive_thresholds import sensitivity_curve
from db.session import get_db
from evaluation.metrics import (
    confusion_matrix,
    first_match_diagnostics,
    j_optimal,
    operating_curve,
)
from evaluation.scenarios import make_normal_scenario, make_struggle_scenario
from learning_analytics.process_state import ProcessRegime
from models.experiment import ExperimentMetrics
from models.session import LearningSession

router = APIRouter()

# Сетка T_k для operating_curve (сек).
_T_K_GRID = [0.0, 15.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 240.0, 300.0]

# Отношения стоимостей для кривой чувствительности.
_RATIOS = [0.2, 0.5, 1.0, 2.0, 5.0]


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Только администратор (зеркало experiment/router._require_admin)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


def _build_synthetic_scenarios():
    """Синтетические сценарии идентификатора (4 типа × 3 onset + 5 нормальных)."""
    scns = []
    for regime in [
        ProcessRegime.REPEATING_ERRORS,
        ProcessRegime.TRIAL_AND_ERROR,
        ProcessRegime.STUCK_ON_STEP,
        ProcessRegime.IDLE,
    ]:
        for onset in [4, 5, 6]:
            scns.append(make_struggle_scenario(regime, onset_index=onset, n=14, step=15.0))
    for _ in range(5):
        scns.append(make_normal_scenario(n=14, step=15.0))
    return scns


def _build_synthetic_sessions():
    """Синтетические сессии для кривой T_k (зеркало derive_thresholds.__main__)."""
    def _session(spell_len: int, regime: str = "stuck_on_step", t_step: int = 15) -> dict:
        samples, t, dwell = [], 0, 0.0
        while t <= spell_len:
            samples.append({"ts": float(t), "regime": regime, "dwell": dwell})
            t += t_step
            dwell += float(t_step)
        samples.append({"ts": float(t), "regime": "productive", "dwell": 0.0})
        return {"samples": samples}

    return [
        _session(30), _session(30), _session(60),
        _session(120), _session(180), _session(300), _session(600),
    ]


def _default_la_config() -> LearningAnalyticsConfig:
    """Конфиг LA без ENV: дефолтные значения Pydantic."""
    return LearningAnalyticsConfig()


def build_identifier_eval(cfg: LearningAnalyticsConfig | None = None) -> dict:
    """Строит operating-кривую + матрицу + first-match на синтетике. preliminary=True."""
    if cfg is None:
        cfg = _default_la_config()

    scns = _build_synthetic_scenarios()
    costs = Costs(
        c_stuck=cfg.cost_stuck,
        c_intervention=cfg.cost_intervention,
        c_false=cfg.cost_false_intervention,
    )
    curve = operating_curve(scns, _T_K_GRID, cfg, costs)
    opt = j_optimal(curve)

    # confusion_matrix: запускаем harness @ j_optimal_t_k
    from evaluation.harness import run_identifier
    pairs = [(scn, run_identifier(scn, opt.t_k, cfg)) for scn in scns]
    cm_raw = confusion_matrix(pairs)
    # сериализуем ключи в str
    cm_ser = {r.value: {c.value: v for c, v in row.items()} for r, row in cm_raw.items()}

    fm = first_match_diagnostics(scns, cfg)

    return {
        "curve": [
            {
                "t_k": p.t_k,
                "latency_median": p.latency_median,
                "false_per_hour": p.false_per_hour,
                "recall": p.recall,
                "j": p.J,
            }
            for p in curve
        ],
        "j_optimal_t_k": opt.t_k,
        "confusion": cm_ser,
        "first_match": fm,
        "costs": {
            "c_stuck": cfg.cost_stuck,
            "c_intervention": cfg.cost_intervention,
            "c_false": cfg.cost_false_intervention,
        },
        # синтетика → всегда предварительно
        "preliminary": True,
    }


def build_tk_sensitivity(cfg: LearningAnalyticsConfig | None = None) -> dict:
    """Кривая чувствительности T_k по ratios стоимостей на синтетических сессиях."""
    if cfg is None:
        cfg = _default_la_config()

    sessions = _build_synthetic_sessions()
    grid = {"stuck_on_step": _T_K_GRID}

    curve = sensitivity_curve(
        sessions,
        _RATIOS,
        grid,
        base_c_intervention=cfg.cost_intervention,
        c_false=cfg.cost_false_intervention,
        cooldown_seconds=cfg.cooldown_period,
        time_unit_seconds=60.0,
    )

    points = []
    for ratio, tk_dict, j in curve:
        # tk_dict: {regime: float}; берём stuck_on_step как представительный
        t_k_val = tk_dict.get("stuck_on_step", 0.0)
        points.append({"ratio": ratio, "t_k": t_k_val, "J": j})

    return {
        "points": points,
        "costs": {
            "c_stuck": cfg.cost_stuck,
            "c_intervention": cfg.cost_intervention,
        },
    }


async def build_overview(db: AsyncSession) -> dict:
    """KPI-агрегат из БД. Числа — из чистых функций."""
    from experiment.analysis import compute_arm_analysis
    from cohort.service import compute_cohort_metrics

    la_cfg = _default_la_config()

    # A/B
    metrics = (await db.execute(select(ExperimentMetrics))).scalars().all()
    ab = compute_arm_analysis(metrics, mentor_seconds=la_cfg.mentor_handling_seconds)

    # Когорта
    cohort = await compute_cohort_metrics(
        db,
        horizon_seconds=la_cfg.cohort_horizon_days * 86400,
        by_arm=False,
    )
    # pooled: агрегируем по всем навыкам
    all_reach = [v.get("reach_rate", 0.0) for v in cohort.values() if isinstance(v, dict)]
    all_n = [v.get("n", 0) for v in cohort.values() if isinstance(v, dict)]
    pooled_reach = sum(all_reach) / len(all_reach) if all_reach else 0.0
    pooled_n = sum(all_n)

    # Идентификатор (синтетика)
    eval_data = build_identifier_eval(la_cfg)

    # Ops
    active = (await db.execute(
        select(func.count(LearningSession.id)).where(LearningSession.status == "active")
    )).scalar() or 0
    total_ivs = (await db.execute(
        select(func.coalesce(func.sum(ExperimentMetrics.interventions_received), 0))
    )).scalar() or 0
    labeled_n = len(metrics)  # реальных записей с метриками

    return {
        "ab": {
            "l2_pass_closed": ab.l2_pass_rate_closed,
            "l2_pass_open": ab.l2_pass_rate_open,
            "mentor_hours_saved": ab.mentor_hours_saved,
        },
        "cohort": {
            "pooled_reach_rate": pooled_reach,
            "pooled_n": pooled_n,
        },
        "identifier": {
            "j_optimal_t_k": eval_data["j_optimal_t_k"],
            "recall_at_opt": eval_data["curve"][
                next(
                    i for i, p in enumerate(eval_data["curve"])
                    if p["t_k"] == eval_data["j_optimal_t_k"]
                )
            ]["recall"] if eval_data["curve"] else 0.0,
            "costs": eval_data["costs"],
        },
        "ops": {
            "active_sessions": active,
            "total_interventions": int(total_ivs),
            "labeled_real_n": labeled_n,
        },
    }


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """KPI-агрегат: A/B, когорта, идентификатор, ops."""
    data = await build_overview(db)
    return OverviewResponse(
        ab=OverviewAb(**data["ab"]),
        cohort=OverviewCohort(**data["cohort"]),
        identifier=OverviewIdentifier(**data["identifier"]),
        ops=OverviewOps(**data["ops"]),
    )


@router.get("/identifier-eval", response_model=IdentifierEvalResponse)
def get_identifier_eval(_: dict = Depends(require_admin)):
    """Operating-кривая идентификатора (синтетика, preliminary=True)."""
    data = build_identifier_eval()
    return IdentifierEvalResponse(
        curve=[CurvePoint(**p) for p in data["curve"]],
        j_optimal_t_k=data["j_optimal_t_k"],
        confusion=data["confusion"],
        first_match=data["first_match"],
        costs=data["costs"],
        preliminary=data["preliminary"],
    )


@router.get("/tk-sensitivity", response_model=TkSensitivityResponse)
def get_tk_sensitivity(_: dict = Depends(require_admin)):
    """Кривая чувствительности T_k по стоимостям (синтетика)."""
    data = build_tk_sensitivity()
    return TkSensitivityResponse(
        points=[TkPoint(**p) for p in data["points"]],
        costs=data["costs"],
    )
