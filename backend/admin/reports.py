"""Report builders behind /admin/overview, /admin/identifier-eval and /admin/tk-sensitivity."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.cohort.service import compute_cohort_metrics
from analytics.criterion import costs_from_config
from analytics.metrics.arm_analysis import compute_arm_analysis
from analytics.metrics.harness import run_identifier
from analytics.metrics.metrics import (
    confusion_matrix,
    first_match_diagnostics,
    j_optimal,
    operating_curve,
)
from analytics.metrics.scenarios import build_synthetic_scenarios, build_synthetic_sessions
from analytics.thresholds import sensitivity_curve
from config.config_model import LearningAnalyticsConfig
from models.learning import LearningSession
from models.research import ExperimentMetrics

# Cost ratios for the sensitivity curve.
_RATIOS = [0.2, 0.5, 1.0, 2.0, 5.0]


def default_la_config() -> LearningAnalyticsConfig:
    """LA config without ENV: default Pydantic values."""
    return LearningAnalyticsConfig()


def build_identifier_eval(cfg: LearningAnalyticsConfig | None = None) -> dict:
    """Operating curve, confusion matrix and first-match on synthetic data."""
    if cfg is None:
        cfg = default_la_config()

    scns = build_synthetic_scenarios()
    curve = operating_curve(scns, cfg.eval_t_k_grid, cfg, costs_from_config(cfg))
    opt = j_optimal(curve)

    pairs = [(scn, run_identifier(scn, opt.t_k, cfg)) for scn in scns]
    cm_ser = {
        row_key.value: {col_key.value: v for col_key, v in row.items()}
        for row_key, row in confusion_matrix(pairs).items()
    }

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
        "first_match": first_match_diagnostics(scns, cfg),
        "costs": {
            "c_stuck": cfg.cost_stuck,
            "c_intervention": cfg.cost_intervention,
            "c_false": cfg.cost_false_intervention,
        },
        # synthetic → always preliminary
        "preliminary": True,
    }


def build_tk_sensitivity(cfg: LearningAnalyticsConfig | None = None) -> dict:
    """T_k sensitivity curve over cost ratios on synthetic sessions."""
    if cfg is None:
        cfg = default_la_config()

    curve = sensitivity_curve(
        build_synthetic_sessions(),
        _RATIOS,
        {"stuck_on_step": cfg.eval_t_k_grid},
        base_c_intervention=cfg.cost_intervention,
        c_false=cfg.cost_false_intervention,
        cooldown_seconds=cfg.cooldown_period,
        time_unit_seconds=60.0,
    )

    return {
        # stuck_on_step is the representative regime
        "points": [
            {"ratio": ratio, "t_k": tk.get("stuck_on_step", 0.0), "J": j} for ratio, tk, j in curve
        ],
        "costs": {
            "c_stuck": cfg.cost_stuck,
            "c_intervention": cfg.cost_intervention,
        },
    }


async def build_overview(db: AsyncSession) -> dict:
    """KPI aggregate from the DB. Numbers come from pure functions."""
    cfg = default_la_config()

    metrics = (await db.execute(select(ExperimentMetrics))).scalars().all()
    ab = compute_arm_analysis(metrics, mentor_seconds=cfg.mentor_handling_seconds)

    cohort = await compute_cohort_metrics(
        db,
        horizon_seconds=cfg.cohort_horizon_days * 86400,
        by_arm=False,
    )
    # aggregate_cohort returns a ready-made pooled cell, not a dict
    pooled = cohort.get("pooled")

    eval_data = build_identifier_eval(cfg)
    curve = eval_data["curve"]
    opt_t_k = eval_data["j_optimal_t_k"]
    recall_at_opt = next((p["recall"] for p in curve if p["t_k"] == opt_t_k), 0.0)

    active = (
        await db.execute(
            select(func.count(LearningSession.id)).where(LearningSession.status == "active")
        )
    ).scalar() or 0
    total_ivs = (
        await db.execute(
            select(func.coalesce(func.sum(ExperimentMetrics.interventions_received), 0))
        )
    ).scalar() or 0

    return {
        "ab": {
            "l2_pass_closed": ab.l2_pass_rate_closed,
            "l2_pass_open": ab.l2_pass_rate_open,
            "mentor_hours_saved": ab.mentor_hours_saved,
        },
        "cohort": {
            "pooled_reach_rate": pooled.time_to_competence.reach_rate if pooled else 0.0,
            "pooled_n": pooled.n if pooled else 0,
        },
        "identifier": {
            "j_optimal_t_k": opt_t_k,
            "recall_at_opt": recall_at_opt,
            "costs": eval_data["costs"],
        },
        "ops": {
            "active_sessions": active,
            "total_interventions": int(total_ivs),
            # sessions with a metrics row, not labeled scenarios
            "finished_sessions_n": len(metrics),
        },
    }
