"""Метрики оценки идентификатора в терминах управления: задержка, ложные/час, recall, CI."""

import random
import statistics
from dataclasses import dataclass

from evaluation.harness import Detection
from evaluation.scenarios import LabeledScenario, is_normal
from evaluation.stats import percentile
from learning_analytics.process_state import ProcessRegime


@dataclass
class DetectionMetrics:
    latency_median: float | None
    latency_p90: float | None
    latency_ci: tuple[float, float] | None
    false_per_hour: float
    recall: float
    n_struggle: int
    n_normal: int
    n_tp: int
    n_misses: int


def _in_window(scn: "LabeledScenario", d: "Detection") -> bool:
    return (
        d.detected
        and d.detected_ts is not None
        and scn.onset_ts is not None
        and scn.onset_ts <= d.detected_ts <= scn.onset_ts + scn.onset_window
    )


def detection_latencies(pairs) -> list[float]:
    return [
        d.detected_ts - scn.onset_ts
        for scn, d in pairs
        if not is_normal(scn) and _in_window(scn, d)
    ]


def bootstrap_ci(values: list[float], n_resamples: int = 1000, seed: int = 0):
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    meds = []
    for _ in range(n_resamples):
        sample = [rng.choice(values) for _ in values]
        meds.append(statistics.median(sample))
    meds.sort()
    # перцентильные индексы по базе (n-1), верхний клампим в границы
    lo = meds[int(0.025 * (n_resamples - 1))]
    hi = meds[min(n_resamples - 1, int(0.975 * (n_resamples - 1)))]
    return (lo, hi)


def _p90(values: list[float]) -> float | None:
    if not values:
        return None
    # Hyndman-Fan Type 7 (numpy/R default), см. evaluation.stats.percentile
    return percentile(values, 90)


def evaluate(pairs) -> "DetectionMetrics":
    struggle = [(scn, d) for scn, d in pairs if not is_normal(scn)]
    normal = [(scn, d) for scn, d in pairs if is_normal(scn)]
    lat = detection_latencies(pairs)
    n_tp = len(lat)
    n_struggle = len(struggle)
    n_false = sum(1 for scn, d in normal if d.detected)
    normal_hours = sum(scn.duration_seconds for scn, _ in normal) / 3600.0
    return DetectionMetrics(
        latency_median=(statistics.median(lat) if lat else None),
        latency_p90=_p90(lat),
        latency_ci=bootstrap_ci(lat),
        false_per_hour=(n_false / normal_hours if normal_hours > 0 else 0.0),
        recall=(n_tp / n_struggle if n_struggle else 0.0),
        n_struggle=n_struggle,
        n_normal=len(normal),
        n_tp=n_tp,
        n_misses=n_struggle - n_tp,
    )


def confusion_matrix(
    pairs: list[tuple[LabeledScenario, Detection]],
) -> dict[ProcessRegime, dict[ProcessRegime, int]]:
    """Матрица ошибок 5×5 (строки=truth, столбцы=detected; None-детект→PRODUCTIVE)."""
    regimes = list(ProcessRegime)
    cm: dict[ProcessRegime, dict[ProcessRegime, int]] = {
        r: dict.fromkeys(regimes, 0) for r in regimes
    }
    for scn, d in pairs:
        truth = scn.truth_regime
        # нет детекта → PRODUCTIVE (не распознан)
        detected = (
            d.detected_regime
            if (d.detected and d.detected_regime is not None)
            else ProcessRegime.PRODUCTIVE
        )
        cm[truth][detected] += 1
    return cm


@dataclass
class OperatingPoint:
    """Точка рабочей кривой идентификатора при заданном пороге T_k."""

    t_k: float
    latency_median: float | None
    false_per_hour: float
    recall: float
    J: float


def operating_curve(scenarios, t_k_grid, config, costs) -> list[OperatingPoint]:
    """Рабочая кривая: метрики + J как функция порога dwell T_k."""
    from control.criterion import BAD_REGIMES
    from control.derive_thresholds import total_J
    from evaluation.harness import run_identifier

    # строим сессии однократно (структура не зависит от t_k)
    sessions: list[dict] = []
    for scn in scenarios:
        samples: list[dict] = []
        for snap in scn.snapshots:
            if scn.onset_ts is not None and snap.ts >= scn.onset_ts:
                regime = scn.truth_regime.value
                dwell = max(0.0, snap.ts - scn.onset_ts)
            else:
                regime = ProcessRegime.PRODUCTIVE.value
                dwell = 0.0
            samples.append({"ts": snap.ts, "regime": regime, "dwell": dwell})
        sessions.append({"samples": samples})

    cooldown = getattr(config, "cooldown_period", 0.0)

    points = []
    for t_k in t_k_grid:
        pairs = [(scn, run_identifier(scn, t_k, config)) for scn in scenarios]
        m = evaluate(pairs)
        thresholds = dict.fromkeys(BAD_REGIMES, t_k)
        j = total_J(sessions, costs, thresholds, cooldown_seconds=cooldown)
        points.append(OperatingPoint(t_k, m.latency_median, m.false_per_hour, m.recall, j))
    return points


def j_optimal(curve: list[OperatingPoint]) -> OperatingPoint:
    """Точка кривой с минимальным J."""
    return min(curve, key=lambda p: p.J)


def first_match_diagnostics(
    scenarios: list[LabeledScenario],
    config,
) -> dict:
    """Диагностика мульти-совпадений: multi_match_rate, order_sensitive_rate, total_firing_snapshots.

    Для каждого снапшота считает, сколько предикатов STRUGGLE_RULES срабатывает.
    multi_match ≥2 → порядок правил определяет результат (order-sensitive).
    Доли считаются от firing-снапшотов (где ≥1 правило сработало).
    """
    from agents.analytics.agent import STRUGGLE_RULES  # отложенный импорт — нет цикла

    firing = 0  # снапшотов, где сработало ≥1 правило
    multi = 0  # снапшотов, где сработало ≥2 правил

    for scn in scenarios:
        for snap in scn.snapshots:
            # каждый элемент STRUGGLE_RULES — кортеж (predicate, stype, interv, conf_fn)
            n_match = sum(1 for pred, *_ in STRUGGLE_RULES if pred(snap.features, config))
            if n_match >= 1:
                firing += 1
            if n_match >= 2:
                multi += 1

    rate = multi / firing if firing else 0.0
    return {
        "total_firing_snapshots": firing,
        "multi_match_rate": rate,
        # order-sensitive ⟺ ≥2 предиката сработало (first-match выбирает первый из них)
        "order_sensitive_rate": rate,
    }
