"""Control criterion J: policy cost over historical state logs."""

import statistics
from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime

from config.config_model import BAD_REGIMES


@dataclass
class Costs:
    """Costs in shared units: stuck time, intervention, false intervention."""

    c_stuck: float
    c_intervention: float
    c_false: float


@dataclass
class JResult:
    """Breakdown of the criterion: J and its terms."""

    J: float
    bad_duration: float
    n_interventions: int
    n_false: int


def costs_from_config(cfg) -> "Costs":
    """Cost vector from LearningAnalyticsConfig, so callers stop hardcoding it."""
    return Costs(
        c_stuck=cfg.cost_stuck,
        c_intervention=cfg.cost_intervention,
        c_false=cfg.cost_false_intervention,
    )


def is_bad_regime(regime: str) -> bool:
    return regime in BAD_REGIMES


def _to_sec(x) -> float:
    """float -- passthrough; datetime -> Unix seconds."""
    if isinstance(x, datetime):
        return x.timestamp()
    return float(x)


def _interventions_outside_bad_regime(samples, intervention_ts) -> int:
    """Counts interventions fired while the process was not in a bad regime.

    Left-edge rule, as for bad_duration. An intervention before the first sample
    isn't counted: the state there is unknown.
    """
    if not samples:
        return 0
    ts = [_to_sec(s["ts"]) for s in samples]
    n_false = 0
    for ivt in intervention_ts:
        idx = bisect_right(ts, ivt) - 1
        if idx < 0:
            continue
        if not is_bad_regime(samples[idx]["regime"]):
            n_false += 1
    return n_false


def _count_false(samples, interventions) -> int:
    """False interventions, two disjoint kinds:

    (a) fired outside any bad regime;
    (b) fired inside a bad spell that ended faster than the median clean self-exit.

    (b) alone misses false alarms on sessions where nothing ever went wrong.
    """
    if not interventions:
        return 0

    ts = [_to_sec(s["ts"]) for s in samples]
    intervention_ts = sorted(_to_sec(iv["ts"]) for iv in interventions)
    n_false = _interventions_outside_bad_regime(samples, intervention_ts)

    # Find all intervals spent in the bad regime (contiguous spells)
    # A spell = a sequence of adjacent bad samples (by the left-edge rule).
    # Collect spells as (start, end, had_intervention).
    spells = []
    i = 0
    n = len(samples)
    while i < n - 1:
        if is_bad_regime(samples[i]["regime"]):
            spell_start = ts[i]
            j = i
            while j < n - 1 and is_bad_regime(samples[j]["regime"]):
                j += 1
            spell_end = ts[j]  # the moment of exit into the productive regime
            recovered = not is_bad_regime(samples[j]["regime"])
            # Is there an intervention inside the spell [spell_start, spell_end)?
            had_iv = any(spell_start <= ivt < spell_end for ivt in intervention_ts)
            spells.append(
                {
                    "start": spell_start,
                    "end": spell_end,
                    "duration": spell_end - spell_start,
                    "recovered": recovered,  # whether it ended via a productive transition
                    "had_iv": had_iv,
                }
            )
            i = j
        else:
            i += 1

    # Median duration of "clean" exits (no intervention, ended productively)
    clean_durations = [sp["duration"] for sp in spells if not sp["had_iv"] and sp["recovered"]]
    if not clean_durations:
        return n_false  # no basis for the spline estimate -- keep only kind (a)

    median_clean = statistics.median(clean_durations)

    # Kind (b): a spell with an intervention that ended faster than the median
    n_false += sum(
        1 for sp in spells if sp["had_iv"] and sp["recovered"] and sp["duration"] < median_clean
    )
    return n_false


def compute_J(samples, interventions, costs, *, bad_duration_samples=None):
    """Policy cost over a session state log.

    samples: [{ts, regime, dwell}] ascending by ts. interventions: [{ts}].
    bad_duration_samples: when given, bad_duration is measured on it (the
    truncated stream the offline optimizer builds) while n_false stays on
    `samples`.

    bad_duration sums the gaps whose left sample is in a bad regime
    (piecewise-constant between polls). See _count_false for the false-alarm rule.
    """
    dur_samples = bad_duration_samples if bad_duration_samples is not None else samples
    ts = [_to_sec(s["ts"]) for s in dur_samples]
    bad_duration = 0.0
    for i in range(len(dur_samples) - 1):
        if is_bad_regime(dur_samples[i]["regime"]):
            bad_duration += ts[i + 1] - ts[i]
    n_interventions = len(interventions)
    n_false = _count_false(samples, interventions)
    J = (
        costs.c_stuck * bad_duration
        + costs.c_intervention * n_interventions
        + costs.c_false * n_false
    )
    return JResult(J=J, bad_duration=bad_duration, n_interventions=n_interventions, n_false=n_false)
