"""Офлайн-вывод порогов dwell T_k по историческим сессиям."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from control.criterion import Costs, _to_sec, compute_J

# Плохие режимы (синхронизировать с criterion.py)
_BAD_REGIMES = {"stuck_on_step", "repeating_errors", "idle", "trial_and_error"}


def _is_bad(regime: str) -> bool:
    return regime in _BAD_REGIMES


def simulate_interventions(
    samples: list[dict],
    dwell_thresholds: dict[str, float],
    cooldown_seconds: float = 0.0,
) -> list[dict]:
    """Симулирует политику вмешательства по порогам dwell + cooldown.

    cooldown_seconds=0 → срабатывает на каждый подходящий сэмпл;
    cooldown_seconds>0 → cooldown блокирует повторный выстрел.
    Алгоритм соответствует живому закону управления в monitor.py.
    """
    interventions: list[dict] = []
    last_fire_ts: float | None = None  # последний выстрел (Unix-сек)

    for s in samples:
        regime = s["regime"]
        if not _is_bad(regime):
            continue  # продуктивный — пропуск

        threshold = dwell_thresholds.get(regime)
        if threshold is None:
            continue  # режим не регулируется

        if s["dwell"] < threshold:
            continue  # ещё не достигли порога

        s_ts = _to_sec(s["ts"])
        # cooldown-гейт: либо первый выстрел, либо пауза достаточна
        if last_fire_ts is not None and s_ts - last_fire_ts < cooldown_seconds:
            continue

        interventions.append({"ts": s_ts})
        last_fire_ts = s_ts

    return interventions


def _truncate_at_interventions(
    samples: list[dict], interventions: list[dict]
) -> list[dict]:
    """Для офлайн-оценки: вмешательство считается завершающим спелл.

    Сэмплы в плохом режиме ПОСЛЕ интервенции (и до конца спелла) заменяются
    продуктивными — симулируем, что агент завершил затруднение.
    Это делает bad_duration зависимым от T_k → оптимизация находит смысловой минимум.
    """
    if not interventions:
        return samples
    iv_ts_sorted = sorted(_to_sec(iv["ts"]) for iv in interventions)
    result = []
    for s in samples:
        s_ts = _to_sec(s["ts"])
        # если этот сэмпл в плохом режиме и после хотя бы одной интервенции — обнуляем
        if _is_bad(s["regime"]) and any(iv_t <= s_ts for iv_t in iv_ts_sorted):
            result.append({**s, "regime": "productive", "dwell": 0.0})
        else:
            result.append(s)
    return result


def total_J(
    sessions: list[dict],
    costs: Costs,
    dwell_thresholds: dict[str, float],
    cooldown_seconds: float = 0.0,
) -> float:
    """Суммарный критерий J по всем сессиям с симулированными вмешательствами.

    bad_duration считается по усечённым сэмплам (интервенция завершает спелл),
    n_false — по оригинальным (нужны clean-выходы для сравнения медиан).
    Без усечения T_k=∞ тривиально побеждает (bad_duration не зависит от T_k).
    """
    total = 0.0
    for s in sessions:
        ivs = simulate_interventions(s["samples"], dwell_thresholds, cooldown_seconds)
        # усечённые сэмплы: после интервенции плохой режим → продуктивный
        truncated = _truncate_at_interventions(s["samples"], ivs)
        total += compute_J(
            s["samples"], ivs, costs, dwell_thresholds,
            bad_duration_samples=truncated,
        ).J
    return total


def derive_T_k(
    sessions: list[dict],
    costs: Costs,
    grid: dict[str, list[float]],
    cooldown_seconds: float = 0.0,
) -> dict[str, float]:
    """Выбирает лучший T_k для каждого режима независимо по сетке кандидатов."""
    # Инициализируем пороги первыми значениями сетки
    current_thresholds: dict[str, float] = {
        regime: candidates[0]
        for regime, candidates in grid.items()
        if candidates
    }

    result: dict[str, float] = {}
    for regime, candidates in grid.items():
        best_tk = candidates[0]
        best_j = float("inf")
        for tk in candidates:
            trial = {**current_thresholds, regime: tk}
            j = total_J(sessions, costs, trial, cooldown_seconds)
            if j < best_j:
                best_j = j
                best_tk = tk
        result[regime] = best_tk
        current_thresholds[regime] = best_tk  # фиксируем для следующих режимов

    return result


def sensitivity_curve(
    sessions: list[dict],
    ratios: list[float],
    grid: dict[str, list[float]],
    base_c_intervention: float = 1.0,
    c_false: float = 2.0,
    cooldown_seconds: float = 0.0,
    time_unit_seconds: float = 1.0,
) -> list[tuple]:
    """Кривая чувствительности T_k по диапазону соотношений стоимостей.

    time_unit_seconds: делитель для c_stuck; = 60 → ratio трактуется как
    «мин затруднения на единицу воздействия», точка безразличия D* = 60/ratio сек.
    c_stuck варьируется по ratio — намеренно (Парето-анализ).
    """
    curve: list[tuple] = []
    for ratio in ratios:
        costs = Costs(
            c_stuck=ratio * base_c_intervention / time_unit_seconds,
            c_intervention=base_c_intervention,
            c_false=c_false,
        )
        tk = derive_T_k(sessions, costs, grid, cooldown_seconds)
        j = total_J(sessions, costs, tk, cooldown_seconds)
        curve.append((ratio, tk, j))
    return curve


# ---------------------------------------------------------------------------
# CLI — синтетические данные или JSON-файл из argv[1]
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    from config.config_model import LearningAnalyticsConfig

    _cfg = LearningAnalyticsConfig()
    # Стоимости из конфига — не хардкод
    _costs_from_config = Costs(
        c_stuck=_cfg.cost_stuck,
        c_intervention=_cfg.cost_intervention,
        c_false=_cfg.cost_false_intervention,
    )
    _cooldown = _cfg.cooldown_period

    def _build_session(
        spell_len: int,
        recover_at: int | None = None,
        regime: str = "stuck_on_step",
        t_step: int = 15,
    ) -> dict:
        """Сессия: плохой спелл длиной spell_len, затем продуктивный.

        recover_at: если задан, вставляет ранний выход в продуктивный режим
        (короткий самовыход, нужен для базы n_false).
        """
        samples: list[dict[str, Any]] = []
        t, dwell = 0, 0.0
        while t <= spell_len:
            samples.append({"ts": float(t), "regime": regime, "dwell": dwell})
            t += t_step
            dwell += float(t_step)
        samples.append({"ts": float(t), "regime": "productive", "dwell": 0.0})
        return {"samples": samples, "interventions": []}

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            sessions = json.load(f)
    else:
        # Данные с вариацией: короткие самовыходы (30-90с) и длинные спеллы (120-600с).
        # base_c_intervention=60 → стоимость воздействия = 1 мин; c_stuck в с⁻¹;
        # при ratio=c_stuck/c_int точка безразличия: D* = c_int/(c_stuck) = 1/ratio мин.
        # ratio=0.2 → D*=5 мин=300с; ratio=5 → D*=12с — кривая гнётся внутри диапазона.
        # Микс спеллов: короткие (30-60с, самовыходы) и длинные (120-600с).
        # D*(ratio) = 60/ratio сек: ratio=0.2→300с, ratio=5→12с — кривая гнётся.
        sessions = [
            _build_session(30),    # 30с — короткий
            _build_session(30),
            _build_session(60),    # 60с
            _build_session(120),   # 120с
            _build_session(180),   # 3 мин
            _build_session(300),   # 5 мин
            _build_session(600),   # 10 мин
        ]

    grid: dict[str, list[float]] = {
        "stuck_on_step": [0.0, 15.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 240.0, 300.0]
    }
    ratios = [0.2, 0.5, 1.0, 2.0, 5.0]

    # time_unit_seconds=60: ratio трактуется как «мин затруднения / воздействие»;
    # точка безразличия D*(ratio) = 60/ratio сек — укладывается в диапазон спеллов (12..300с).
    best = derive_T_k(sessions, _costs_from_config, grid, cooldown_seconds=_cooldown)
    curve = sensitivity_curve(
        sessions, ratios, grid,
        base_c_intervention=_cfg.cost_intervention,
        c_false=_cfg.cost_false_intervention,
        cooldown_seconds=_cooldown,
        time_unit_seconds=60.0,  # ratio в мин⁻¹; D*(ratio)=60/ratio сек
    )

    # Пишем отчёт
    out_dir = Path(__file__).parents[2] / "docs" / "superpowers" / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / "T_k_sensitivity.md"

    lines = [
        "# T_k sensitivity report",
        "",
        f"**Конфиг-стоимости**: c_stuck={_cfg.cost_stuck}, c_int={_cfg.cost_intervention}, c_false={_cfg.cost_false_intervention}",
        f"**Cooldown (из конфига)**: {_cooldown}s",
        "",
        f"**Оптимальные пороги** (c_stuck={_cfg.cost_stuck}, c_int={_cfg.cost_intervention}, c_false={_cfg.cost_false_intervention}): `{best}`",
        "",
        "## Кривая чувствительности",
        "",
        "| ratio (c_stuck/c_int) | T_k | J |",
        "|-|-|-|",
    ]
    for ratio, tk, j in curve:
        lines.append(f"| {ratio} | {tk} | {j:.2f} |")

    report.write_text("\n".join(lines) + "\n")
    print(f"Report written to {report}")
    print(f"Best T_k (costs from config): {best}")
    for pt in curve:
        print(f"  ratio={pt[0]}: T_k={pt[1]}, J={pt[2]:.2f}")
