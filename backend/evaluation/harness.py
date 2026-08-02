"""Runs the P1 identifier (full feature->rule->dwell pipeline) over a scenario at threshold T_k."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from agents.identifier.agent import identify_regime
from config.config_model import LearningAnalyticsConfig
from evaluation.scenarios import LabeledScenario
from learning_analytics.process_state import DwellTracker, ProcessRegime, analysis_to_regime, is_bad

# Fixed base for converting snap.ts (float, seconds) -> datetime
_BASE = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass
class Detection:
    detected: bool
    detected_ts: float | None
    detected_regime: ProcessRegime | None


def run_identifier(
    scenario: LabeledScenario, t_k: float, config: LearningAnalyticsConfig
) -> Detection:
    """Runs the full pipeline over the scenario's snapshots at dwell threshold T_k."""
    for sample in identifier_trace(scenario, config):
        if is_bad(ProcessRegime(sample["regime"])) and sample["dwell"] >= t_k:
            return Detection(True, sample["ts"], ProcessRegime(sample["regime"]))
    return Detection(False, None, None)


def identifier_trace(scenario: LabeledScenario, config: LearningAnalyticsConfig) -> list[dict]:
    """Per-snapshot state as the identifier sees it: {ts, regime, dwell}.

    Threshold-free: T_k only gates firing, so one trace serves the whole grid.
    """
    tracker = DwellTracker()
    trace: list[dict] = []
    for snap in scenario.snapshots:
        result = identify_regime(snap.features, config)
        regime = analysis_to_regime(result)
        dwell = tracker.observe(regime, _BASE + timedelta(seconds=snap.ts))
        trace.append({"ts": snap.ts, "regime": regime.value, "dwell": dwell})
    return trace
