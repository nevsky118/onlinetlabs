"""Control criterion J: policy cost over historical state logs."""

import statistics
from dataclasses import dataclass
from datetime import datetime


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


BAD_REGIMES = {"stuck_on_step", "repeating_errors", "idle", "trial_and_error"}


def is_bad_regime(regime: str) -> bool:
    return regime in BAD_REGIMES


def _to_sec(x) -> float:
    """float -- passthrough; datetime -> Unix seconds."""
    if isinstance(x, datetime):
        return x.timestamp()
    return float(x)


def _count_false(samples, interventions) -> int:
    """False intervention: an intervention after which the bad regime ended
    faster than the median "clean" self-exit (without intervention).

    Spline assumption: state is piecewise-constant between polls.
    If there are no clean exits, we don't count any false ones (conservative).
    """
    if not interventions:
        return 0

    ts = [_to_sec(s["ts"]) for s in samples]
    intervention_ts = sorted(_to_sec(iv["ts"]) for iv in interventions)

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
        return 0  # no basis for estimation -- don't count false ones

    median_clean = statistics.median(clean_durations)

    # False intervention: a spell with an intervention that ended faster than the median
    n_false = sum(
        1 for sp in spells if sp["had_iv"] and sp["recovered"] and sp["duration"] < median_clean
    )
    return n_false


def compute_J(samples, interventions, costs, *, bad_duration_samples=None):
    """Policy cost over a session state log.

    samples: list of dicts {ts: float|datetime, regime: str, dwell: float}, ascending by ts.
    interventions: list of dicts {ts: float|datetime}.
    bad_duration_samples: if given, bad_duration is computed from it (truncated samples
      for the offline optimizer), while n_false uses the original samples.
    bad_duration = total duration of intervals between adjacent samples where
      the left sample is in a bad regime (piecewise-constant state between polls).
    False intervention (default strategy, documented as a spline assumption):
      an intervention after which the process returned to the productive regime
      faster than the median time of spontaneous exit from that regime over
      intervals WITHOUT an intervention. If the median can't be estimated
      (no "clean" exits), we don't count any false ones (conservative).
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
