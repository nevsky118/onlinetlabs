"""Defense export of all metrics of the 2.3.4 control loop → stdout plus an md artifact."""

import asyncio
from pathlib import Path

from sqlalchemy import select

from analytics.cohort.metrics import retention_metric
from analytics.cohort.report import render_cohort_table
from analytics.cohort.service import compute_cohort_metrics
from analytics.criterion import costs_from_config
from analytics.metrics.arm_analysis import compute_arm_analysis
from analytics.metrics.harness import run_identifier
from analytics.metrics.help_dependence import help_dependence_trajectory, is_declining
from analytics.metrics.metrics import (
    confusion_matrix,
    first_match_diagnostics,
    j_optimal,
    operating_curve,
)
from analytics.metrics.scenarios import build_synthetic_scenarios, build_synthetic_sessions
from analytics.runtime.latency import stage_percentiles
from analytics.runtime.process_state import ProcessRegime
from analytics.thresholds import sensitivity_curve
from config.config_model import LearningAnalyticsConfig
from config.env_config_loader import load_settings
from kit.db import async_session
from models.learning import LearningSession
from models.research import ExperimentMetrics

_REGIMES = [
    ProcessRegime.PRODUCTIVE,
    ProcessRegime.REPEATING_ERRORS,
    ProcessRegime.TRIAL_AND_ERROR,
    ProcessRegime.STUCK_ON_STEP,
    ProcessRegime.IDLE,
]
_LABELS = {
    ProcessRegime.PRODUCTIVE: "PROD",
    ProcessRegime.REPEATING_ERRORS: "REP",
    ProcessRegime.TRIAL_AND_ERROR: "T&E",
    ProcessRegime.STUCK_ON_STEP: "STUCK",
    ProcessRegime.IDLE: "IDLE",
}


def _section_ab(lines, db_metrics, cfg):
    """Section 1. A/B effect computed via compute_arm_analysis."""

    r = compute_arm_analysis(db_metrics, mentor_seconds=cfg.mentor_handling_seconds)
    lines += [
        "## 1. A/B-эффект",
        "",
        f"_Параметр_: mentor_handling_seconds={cfg.mentor_handling_seconds}",
        "",
        "| Метрика | open | closed |",
        "|-|-|-|",
        f"| L2 pass rate | {r.l2_pass_rate_open:.3f} | {r.l2_pass_rate_closed:.3f} |",
        f"| escalations mean | {r.escalations_mean_open:.2f} | {r.escalations_mean_closed:.2f} |",
        f"| ч наставника сохранено | {r.mentor_hours_saved:.2f} | — |",
    ]
    ec = r.repeated_errors_comparison
    if ec.get("t_statistic") is not None:
        lines += [
            "",
            "**Повторные ошибки (Welch t-test)**",
            "",
            "| | open | closed |",
            "|-|-|-|",
            f"| mean | {ec['group_a_mean']} | {ec['group_b_mean']} |",
            f"| reduction % | {ec['reduction_percent']} | — |",
            f"| t | {ec['t_statistic']} | p={ec['p_value']} |",
            f"| Cohen's d | {ec['cohens_d']} | sig={ec['significant']} |",
        ]
    else:
        lines.append(f"\n> {ec.get('error', 'Нет данных')}")
    lines += [
        "",
        "_Дельта плеч — каузально (рандомизация). Ч наставника = контрфактуал A/B, не сырые обращения._",
        "",
    ]


async def _section_latency(lines, db):
    """Section 5. Closed-loop cycle latency."""

    pct = await stage_percentiles(db, "analysis", [50, 95, 99])
    lines += [
        "## 5. Латентность цикла",
        "",
        "| стадия | p50 (мс) | p95 (мс) | p99 (мс) |",
        "|-|-|-|-|",
        f"| analysis | {pct.get(50, 0.0):.1f} | {pct.get(95, 0.0):.1f} | {pct.get(99, 0.0):.1f} |",
        "",
        "_Пусто, если LA_LATENCY_CAPTURE_ENABLED выключен._",
        "",
    ]


async def _section_help_dependence(lines, db):
    """Section 6. Help-dependence trajectory (MRT secondary endpoint)."""

    session_ids = [
        str(sid)
        for sid in (
            await db.execute(select(LearningSession.id).order_by(LearningSession.started_at))
        )
        .scalars()
        .all()
    ]
    counts = await help_dependence_trajectory(db, session_ids)
    lines += [
        "## 6. Help-dependence",
        "",
        f"_Сессий_: {len(counts)}; траектория: {counts if counts else '—'}",
        f"_Убывает_: {'да' if counts and is_declining(counts) else 'нет'}",
        "",
    ]


async def _section_retention(lines, db):
    """Section 7. Retention (opportunistic, explicitly not a result)."""

    retests = [
        bool(flag)
        for flag in (
            await db.execute(
                select(ExperimentMetrics.l2_unassisted_pass).where(
                    ExperimentMetrics.l2_unassisted_pass.isnot(None)
                )
            )
        )
        .scalars()
        .all()
    ]
    r = retention_metric(retests)
    rate = "—" if r.retest_pass_rate is None else f"{r.retest_pass_rate:.2f}"
    lines += [
        "## 7. Retention",
        "",
        f"_Ретестов_: {r.retest_count}; доля успешных: {rate}",
        "",
        f"> {r.note}",
        "",
    ]


async def _section_cohort(lines, db, cfg):
    """Section 2. Cohort metrics per skill."""

    horizon = cfg.cohort_horizon_days * 86400.0
    out = await compute_cohort_metrics(db, horizon_seconds=horizon, by_arm=True)
    lines += [
        "## 2. Когорта",
        "",
        f"_Параметры_: horizon={cfg.cohort_horizon_days} дн., headline={out['headline_arm']}",
        "",
    ]
    lines += render_cohort_table(
        out["by_skill"] + [out["pooled"]],
        ["stratum", "n", "censored", "reach", "median_calendar", "median_active", "interventions"],
    )
    lines += [
        "",
        "_Survivorship-предупреждение. KM-медиана при <50% дошедших → reach@T / restricted-mean. Headline=closed._",
        "",
    ]


def _section_identifier(lines, cfg):
    """Section 3. Operating curve, confusion matrix and first-match (synthetic)."""

    costs = costs_from_config(cfg)
    lines += [
        "## 3. Идентификатор П1",
        "",
        f"_Стоимости_: c_застр={costs.c_stuck}, c_возд={costs.c_intervention}, "
        f"c_ложн={costs.c_false}",
        "",
    ]

    scns = build_synthetic_scenarios()
    curve = operating_curve(scns, cfg.eval_t_k_grid, cfg, costs)
    best = j_optimal(curve)

    lines += [
        "### 3a. Рабочая кривая",
        "",
        "| T_k (с) | latency медиана (с) | ложные/час | recall | J |",
        "|-|-|-|-|-|",
    ]
    for p in curve:
        lat = "—" if p.latency_median is None else f"{p.latency_median:.1f}"
        marker = " *" if p is best else ""
        lines.append(
            f"| {p.t_k:.0f}{marker} | {lat} | {p.false_per_hour:.2f} | {p.recall:.2f} | {p.J:.2f} |"
        )
    lines += [f"\n_* J-оптимум при T_k={best.t_k:.0f}с_", ""]

    # matrix @ J-optimum
    pairs_best = [(scn, run_identifier(scn, best.t_k, cfg)) for scn in scns]
    cm = confusion_matrix(pairs_best)
    header_cols = " | ".join(_LABELS[r] for r in _REGIMES)
    lines += [
        "### 3b. Матрица путаницы 5×5 @ J-оптимум",
        "",
        f"| truth\\pred | {header_cols} |",
        "|" + "-|" * (len(_REGIMES) + 1),
    ]
    for truth in _REGIMES:
        row = " | ".join(str(cm[truth][pred]) for pred in _REGIMES)
        lines.append(f"| {_LABELS[truth]} | {row} |")

    # first-match
    diag = first_match_diagnostics(scns, cfg)
    lines += [
        "",
        "### 3c. First-match диагностика",
        "",
        f"- total_firing_snapshots: {diag['total_firing_snapshots']}",
        f"- multi_match_rate: {diag['multi_match_rate']:.3f}",
        f"- order_sensitive_rate: {diag['order_sensitive_rate']:.3f}",
        "",
        "_Rate > F1 (управленческая цена ошибки). Синтетика — предварительно. "
        "Заменяет внешние PoC-числа до накопления разметки._",
        "",
    ]


def _section_tk(lines, cfg):
    """Section 4. T_k sensitivity curve."""

    sessions = build_synthetic_sessions()
    grid = {"stuck_on_step": [0.0, 15.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 240.0, 300.0]}
    ratios = [0.2, 0.5, 1.0, 2.0, 5.0]

    c_int = cfg.cost_intervention
    c_false = cfg.cost_false_intervention

    lines += [
        "## 4. Закон T_k",
        "",
        f"_Стоимости_: c_возд={c_int}, c_ложн={c_false}; c_застр варьируется по ratio.",
        f"_Cooldown_: {cfg.cooldown_period}с",
        "",
    ]

    curve = sensitivity_curve(
        sessions,
        ratios,
        grid,
        base_c_intervention=c_int,
        c_false=c_false,
        cooldown_seconds=cfg.cooldown_period,
        time_unit_seconds=60.0,  # ratio = min⁻¹; D*(ratio)=60/ratio sec
    )

    lines += [
        "| ratio (c_застр/c_возд) | c_застр | T_k (stuck_on_step, с) | J |",
        "|-|-|-|-|",
    ]
    for ratio, tk, j in curve:
        c_stuck = ratio * c_int / 60.0
        lines.append(f"| {ratio} | {c_stuck:.4f} | {tk.get('stuck_on_step', '—')} | {j:.2f} |")

    lines += [
        "",
        "_T_k — не одно число: кривая гнётся со стоимостью. D*(ratio)=60/ratio сек._",
        "",
    ]


async def main():
    # lazy db import, only for a real run
    try:
        cfg_obj = load_settings()
        cfg = cfg_obj.learning_analytics
    except Exception:
        cfg = LearningAnalyticsConfig()

    lines = [
        "# Защитные метрики контура 2.3.4",
        "",
        f"_c_застр={cfg.cost_stuck}, c_возд={cfg.cost_intervention}, "
        f"c_ложн={cfg.cost_false_intervention}, cooldown={cfg.cooldown_period}с_",
        "",
    ]

    # Section order 1→2→3→4 (the logical one for the defense). Sections 1+2 require the DB.
    try:
        async with async_session() as db:
            db_metrics = (await db.execute(select(ExperimentMetrics))).scalars().all()
            _section_ab(lines, db_metrics, cfg)
            await _section_cohort(lines, db, cfg)
    except Exception as exc:
        lines += [
            "## 1. A/B-эффект",
            "",
            f"> БД недоступна: {exc}",
            "",
            "## 2. Когорта",
            "",
            f"> БД недоступна: {exc}",
            "",
        ]

    # Sections 3+4 (synthetic, no DB) come after
    _section_identifier(lines, cfg)
    _section_tk(lines, cfg)

    # Sections 5-7 need the DB; each degrades to a note rather than sinking the report.
    try:
        async with async_session() as db:
            await _section_latency(lines, db)
            await _section_help_dependence(lines, db)
            await _section_retention(lines, db)
    except Exception as exc:
        lines += [
            "## 5-7. Латентность, help-dependence, retention",
            "",
            f"> БД недоступна: {exc}",
            "",
        ]

    report = "\n".join(lines)
    print(report)

    # write the artifact
    out_dir = Path(__file__).parents[2] / "docs" / "superpowers" / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "defense_metrics.md").write_text(report + "\n")


if __name__ == "__main__":
    asyncio.run(main())
