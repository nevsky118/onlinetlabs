"""Отчёт по оценке идентификатора П1: рабочая кривая + матрица путаницы + first-match."""

import asyncio

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

# Порядок режимов для матрицы 5×5
_REGIMES = [
    ProcessRegime.PRODUCTIVE,
    ProcessRegime.REPEATING_ERRORS,
    ProcessRegime.TRIAL_AND_ERROR,
    ProcessRegime.STUCK_ON_STEP,
    ProcessRegime.IDLE,
]

# Человекочитаемые метки
_LABELS = {
    ProcessRegime.PRODUCTIVE: "PROD",
    ProcessRegime.REPEATING_ERRORS: "REP",
    ProcessRegime.TRIAL_AND_ERROR: "T&E",
    ProcessRegime.STUCK_ON_STEP: "STUCK",
    ProcessRegime.IDLE: "IDLE",
}


def _build_synthetic():
    """3-5 сценариев на каждый тип + 5 нормальных."""
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


def _per_type_recall(pairs, curve_t_k, config) -> dict[ProcessRegime, float]:
    """Recall по каждому типу при данном T_k."""
    from evaluation.harness import run_identifier
    from evaluation.scenarios import is_normal

    type_tp: dict[ProcessRegime, int] = {}
    type_n: dict[ProcessRegime, int] = {}
    for scn in [s for s, _ in pairs]:
        if is_normal(scn):
            continue
        r = scn.truth_regime
        type_n[r] = type_n.get(r, 0) + 1
        d = run_identifier(scn, curve_t_k, config)
        in_win = (
            d.detected
            and d.detected_ts is not None
            and scn.onset_ts is not None
            and scn.onset_ts <= d.detected_ts <= scn.onset_ts + scn.onset_window
        )
        if in_win:
            type_tp[r] = type_tp.get(r, 0) + 1
    return {r: type_tp.get(r, 0) / n for r, n in type_n.items()}


async def main():
    # Конфиг и стоимости
    try:
        settings = load_settings()
        cfg = settings.learning_analytics
    except Exception:
        from config.config_model import LearningAnalyticsConfig

        cfg = LearningAnalyticsConfig()

    costs = Costs(c_stuck=1.0, c_intervention=1.0, c_false=5.0)

    # Синтетический датасет (всегда)
    scns = _build_synthetic()

    # Без реального харвестинга (не подключён к БД в этом режиме) labeled-real-N остаётся 0
    labeled_real_n = 0

    n_synth = sum(1 for s in scns if s.source == "synthetic")
    n_real = sum(1 for s in scns if s.source == "real")

    # Рабочая кривая
    curve = operating_curve(scns, cfg.eval_t_k_grid, cfg, costs)
    best = j_optimal(curve)

    # Матрица и recall на J-оптимальном T_k
    from evaluation.harness import run_identifier

    pairs_best = [(scn, run_identifier(scn, best.t_k, cfg)) for scn in scns]
    cm = confusion_matrix(pairs_best)
    per_type = _per_type_recall(pairs_best, best.t_k, cfg)
    diag = first_match_diagnostics(scns, cfg)

    # ── (a) Рабочая кривая ───────────────────────────────────────────────────
    print("# Оценка идентификатора П1 — рабочая кривая\n")
    print("| T_k (с) | latency медиана (с) | ложные/час | recall | J |")
    print("|-|-|-|-|-|")
    for p in curve:
        lat = "—" if p.latency_median is None else f"{p.latency_median:.1f}"
        marker = " *" if p is best else ""
        print(
            f"| {p.t_k:.0f}{marker} | {lat} | {p.false_per_hour:.2f} | {p.recall:.2f} | {p.J:.2f} |"
        )

    print(f"\n_* J-оптимум при T_k={best.t_k:.0f}с_\n")

    # ── (b) Матрица путаницы 5×5 ─────────────────────────────────────────────
    print("## Матрица путаницы 5×5 @ J-оптимум\n")
    header_cols = " | ".join(_LABELS[r] for r in _REGIMES)
    print(f"| truth\\pred | {header_cols} |")
    print("|" + "-|" * (len(_REGIMES) + 1))
    for truth in _REGIMES:
        row = " | ".join(str(cm[truth][pred]) for pred in _REGIMES)
        print(f"| {_LABELS[truth]} | {row} |")
    print()

    # ── (c) Per-type recall ──────────────────────────────────────────────────
    print("## Recall по типу @ J-оптимум\n")
    print("| Тип | recall |")
    print("|-|-|")
    for r, rec in per_type.items():
        print(f"| {_LABELS[r]} | {rec:.2f} |")
    print()

    # ── (d) First-match диагностика ─────────────────────────────────────────
    print("## First-match диагностика\n")
    print(f"- total_firing_snapshots: {diag['total_firing_snapshots']}")
    print(f"- multi_match_rate: {diag['multi_match_rate']:.3f}")
    print(f"- order_sensitive_rate: {diag['order_sensitive_rate']:.3f}")
    print()

    # ── (e) Split synth/real + labeled-real-N ───────────────────────────────
    print("## Датасет\n")
    print(f"- synthetic: {n_synth}")
    print(f"- real (harvested): {n_real}")
    print(f"- labeled-real-N: {labeled_real_n}")
    if labeled_real_n < 10:
        print("\n> ⚠ **Предварительно**: labeled-real-N < 10; метрики только по синтетике.")
    print()

    # ── (f) Методологическое примечание ─────────────────────────────────────
    print(
        "> **NOTE:** Плоский T_k — операционная характеристика идентификатора; "
        "per-regime пороги dwell_thresholds выводятся в Задаче 2 (derive_thresholds)."
    )


if __name__ == "__main__":
    asyncio.run(main())
