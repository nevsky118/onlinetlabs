"""Защитный экспорт всех метрик контура 2.3.4 → stdout + md-артефакт."""

import asyncio
from pathlib import Path

from config.env_config_loader import load_settings
from control.criterion import Costs
from evaluation.metrics import (
    confusion_matrix,
    first_match_diagnostics,
    j_optimal,
    operating_curve,
)
from evaluation.scenarios import (
    make_normal_scenario,
    make_struggle_scenario,
)
from learning_analytics.process_state import ProcessRegime

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


def _fmt_days(seconds):
    return "—" if seconds is None else f"{seconds / 86400.0:.1f} дн"


def _build_synthetic_scenarios():
    """Сценарии идентификатора: 3 onset × 4 типа + 5 нормальных (зеркало eval_identifier)."""
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
    """Синтет-сессии для кривой T_k (зеркало derive_thresholds.__main__)."""

    def _session(spell_len, regime="stuck_on_step", t_step=15):
        samples, t, dwell = [], 0, 0.0
        while t <= spell_len:
            samples.append({"ts": float(t), "regime": regime, "dwell": dwell})
            t += t_step
            dwell += float(t_step)
        samples.append({"ts": float(t), "regime": "productive", "dwell": 0.0})
        return {"samples": samples}

    return [
        _session(30),
        _session(30),
        _session(60),
        _session(120),
        _session(180),
        _session(300),
        _session(600),
    ]


def _section_ab(lines, db_metrics, cfg):
    """Секция 1: A/B-эффект через compute_arm_analysis."""
    from experiment.analysis import compute_arm_analysis

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


async def _section_cohort(lines, db, cfg):
    """Секция 2: когортные метрики по навыку."""
    from cohort.service import compute_cohort_metrics

    horizon = cfg.cohort_horizon_days * 86400.0
    out = await compute_cohort_metrics(db, horizon_seconds=horizon, by_arm=True)
    lines += [
        "## 2. Когорта",
        "",
        f"_Параметры_: horizon={cfg.cohort_horizon_days} дн., headline={out['headline_arm']}",
        "",
        "| Страта | n | цензур | reach L2 | медиана кал. | медиана акт. | возд. L1→L2 |",
        "|-|-|-|-|-|-|-|",
    ]
    for cell in out["by_skill"] + [out["pooled"]]:
        t, a = cell.time_to_competence, cell.autonomy
        label = cell.skill or "ПУЛ"
        l2i = "—" if a.mean_l2_interventions is None else f"{a.mean_l2_interventions:.1f}"
        lines.append(
            f"| {label} | {t.n} | {t.censored} | {t.reach_rate:.2f} | "
            f"{_fmt_days(t.median_calendar_seconds)} | {_fmt_days(t.median_active_seconds)} | "
            f"{a.mean_l1_interventions:.1f}→{l2i} |"
        )
    lines += [
        "",
        "_Survivorship-предупреждение. KM-медиана при <50% дошедших → reach@T / restricted-mean. Headline=closed._",
        "",
    ]


def _section_identifier(lines, cfg):
    """Секция 3: рабочая кривая + матрица + first-match (синтетика)."""
    from evaluation.harness import run_identifier

    # стоимости из конфига
    costs = Costs(
        c_stuck=cfg.cost_stuck,
        c_intervention=cfg.cost_intervention,
        c_false=cfg.cost_false_intervention,
    )
    lines += [
        "## 3. Идентификатор П1",
        "",
        f"_Стоимости_: c_застр={costs.c_stuck}, c_возд={costs.c_intervention}, "
        f"c_ложн={costs.c_false}",
        "",
    ]

    scns = _build_synthetic_scenarios()
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

    # матрица @ J-оптимум
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
    """Секция 4: кривая чувствительности T_k."""
    from control.derive_thresholds import sensitivity_curve

    sessions = _build_synthetic_sessions()
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
        time_unit_seconds=60.0,  # ratio = мин⁻¹; D*(ratio)=60/ratio сек
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
    # ленивый импорт db — только при реальном прогоне
    try:
        cfg_obj = load_settings()
        cfg = cfg_obj.learning_analytics
    except Exception:
        from config.config_model import LearningAnalyticsConfig

        cfg = LearningAnalyticsConfig()

    lines = [
        "# Защитные метрики контура 2.3.4",
        "",
        f"_c_застр={cfg.cost_stuck}, c_возд={cfg.cost_intervention}, "
        f"c_ложн={cfg.cost_false_intervention}, cooldown={cfg.cooldown_period}с_",
        "",
    ]

    # Порядок секций 1→2→3→4 (логичный для защиты). Секции 1+2 требуют БД.
    try:
        from sqlalchemy import select

        from db.session import async_session
        from models.experiment import ExperimentMetrics

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

    # Секции 3+4 (синтетика, без БД) — после
    _section_identifier(lines, cfg)
    _section_tk(lines, cfg)

    report = "\n".join(lines)
    print(report)

    # пишем артефакт
    out_dir = Path(__file__).parents[2] / "docs" / "superpowers" / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "defense_metrics.md").write_text(report + "\n")


if __name__ == "__main__":
    asyncio.run(main())
