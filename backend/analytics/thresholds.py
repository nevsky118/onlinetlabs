"""Offline derivation of dwell thresholds T_k from historical sessions."""

from __future__ import annotations

from collections.abc import Callable

from analytics.criterion import Costs, _to_sec, compute_J, is_bad_regime

# Counterfactual: (samples, interventions) -> samples for computing bad_duration.
# Stipulation (truncation) vs measured hazard (P4) -- the de-circularization ablation axis.
Counterfactual = Callable[[list[dict], list[dict]], list[dict]]


def simulate_interventions(
    samples: list[dict],
    dwell_thresholds: dict[str, float],
    cooldown_seconds: float = 0.0,
) -> list[dict]:
    """Simulates the intervention policy from dwell thresholds + cooldown.

    cooldown_seconds=0 -> fires on every qualifying sample;
    cooldown_seconds>0 -> cooldown blocks a repeat firing.
    The algorithm matches the live control law in monitor.py.
    """
    interventions: list[dict] = []
    last_fire_ts: float | None = None  # last firing (Unix seconds)

    for s in samples:
        regime = s["regime"]
        if not is_bad_regime(regime):
            continue  # productive -- skip

        threshold = dwell_thresholds.get(regime)
        if threshold is None:
            continue  # regime isn't regulated

        if s["dwell"] < threshold:
            continue  # threshold not reached yet

        s_ts = _to_sec(s["ts"])
        # cooldown gate: either the first firing, or the pause is long enough
        if last_fire_ts is not None and s_ts - last_fire_ts < cooldown_seconds:
            continue

        interventions.append({"ts": s_ts})
        last_fire_ts = s_ts

    return interventions


def _truncate_at_interventions(samples: list[dict], interventions: list[dict]) -> list[dict]:
    """For offline evaluation: an intervention is treated as ending the spell.

    Bad-regime samples AFTER the intervention (and until the spell ends) are
    replaced with productive ones -- simulating that the agent resolved the struggle.
    This makes bad_duration depend on T_k -> optimization finds a meaningful minimum.
    """
    if not interventions:
        return samples
    iv_ts_sorted = sorted(_to_sec(iv["ts"]) for iv in interventions)
    result = []
    for s in samples:
        s_ts = _to_sec(s["ts"])
        # if this sample is in a bad regime and after at least one intervention -- zero it out
        if is_bad_regime(s["regime"]) and any(iv_t <= s_ts for iv_t in iv_ts_sorted):
            result.append({**s, "regime": "productive", "dwell": 0.0})
        else:
            result.append(s)
    return result


def no_effect_counterfactual(samples: list[dict], interventions: list[dict]) -> list[dict]:
    """Counterfactual "the intervention does NOT affect the outcome": bad_duration doesn't depend on T_k.

    An ablation alternative to the _truncate_at_interventions stipulation: shows that
    the T_k optimum is a property of the ASSUMPTION about effect, not just the data. On
    real logs, its place is taken by a counterfactual from MEASURED hazard (P4), not an assumption.
    """
    return samples


def total_J(
    sessions: list[dict],
    costs: Costs,
    dwell_thresholds: dict[str, float],
    cooldown_seconds: float = 0.0,
    counterfactual: Counterfactual = _truncate_at_interventions,
) -> float:
    """Total criterion J summed over all sessions with simulated interventions.

    bad_duration is computed from counterfactual samples (intervention effect),
    n_false from the original ones (clean exits are needed to compare medians).
    The default counterfactual is the stipulation (intervention ends the spell); without
    dependence on T_k (no_effect_counterfactual), T_k=inf trivially wins.

    Optional `detections` (regime/dwell as the identifier reported them) drives
    firing; costs are always charged against `samples`. Without it firing is read
    off `samples`, i.e. a perfect detector -- an oracle bound, not a realized J.
    """
    total = 0.0
    for s in sessions:
        firing_samples = s.get("detections") or s["samples"]
        ivs = simulate_interventions(firing_samples, dwell_thresholds, cooldown_seconds)
        # bad_duration from the counterfactual: the intervention's effect on the outcome
        truncated = counterfactual(s["samples"], ivs)
        total += compute_J(
            s["samples"],
            ivs,
            costs,
            bad_duration_samples=truncated,
        ).J
    return total


def derive_T_k(
    sessions: list[dict],
    costs: Costs,
    grid: dict[str, list[float]],
    cooldown_seconds: float = 0.0,
    counterfactual: Counterfactual = _truncate_at_interventions,
) -> dict[str, float]:
    """Selects the best T_k for each regime independently over a candidate grid."""
    # Initialize thresholds with the grid's first values
    current_thresholds: dict[str, float] = {
        regime: candidates[0] for regime, candidates in grid.items() if candidates
    }

    result: dict[str, float] = {}
    for regime, candidates in grid.items():
        best_tk = candidates[0]
        best_j = float("inf")
        for tk in candidates:
            trial = {**current_thresholds, regime: tk}
            j = total_J(sessions, costs, trial, cooldown_seconds, counterfactual)
            if j < best_j:
                best_j = j
                best_tk = tk
        result[regime] = best_tk
        current_thresholds[regime] = best_tk  # lock in for subsequent regimes

    return result


def sensitivity_curve(
    sessions: list[dict],
    ratios: list[float],
    grid: dict[str, list[float]],
    base_c_intervention: float = 1.0,
    c_false: float = 2.0,
    cooldown_seconds: float = 0.0,
    time_unit_seconds: float = 1.0,
    counterfactual: Counterfactual = _truncate_at_interventions,
) -> list[tuple]:
    """Sensitivity curve of T_k over a range of cost ratios.

    time_unit_seconds: divisor for c_stuck; =60 -> ratio is interpreted as
    "minutes stuck per unit of intervention", indifference point D* = 60/ratio sec.
    c_stuck varies with ratio -- intentionally (Pareto analysis).
    """
    curve: list[tuple] = []
    for ratio in ratios:
        costs = Costs(
            c_stuck=ratio * base_c_intervention / time_unit_seconds,
            c_intervention=base_c_intervention,
            c_false=c_false,
        )
        tk = derive_T_k(sessions, costs, grid, cooldown_seconds, counterfactual)
        j = total_J(sessions, costs, tk, cooldown_seconds, counterfactual)
        curve.append((ratio, tk, j))
    return curve
