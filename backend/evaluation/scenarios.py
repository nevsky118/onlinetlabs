"""Labeled scenarios for evaluating the P1 identifier (synthetic + loaded real)."""

from dataclasses import dataclass
from datetime import UTC, datetime

from agents.identifier.models import SessionFeatures
from learning_analytics.process_state import ProcessRegime

# Fixed timestamp for synthetic snapshots (computed_at -- a required field)
_EPOCH = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass
class Snapshot:
    ts: float  # seconds from session start
    features: SessionFeatures


@dataclass
class LabeledScenario:
    snapshots: list["Snapshot"]
    onset_ts: float | None  # None iff a normal session
    onset_window: float  # +/-delta tolerance (sec)
    truth_regime: ProcessRegime
    duration_seconds: float
    source: str  # "synthetic" | "real"


def is_normal(s: "LabeledScenario") -> bool:
    return s.truth_regime == ProcessRegime.PRODUCTIVE


def _features(ts_index: int, regime: ProcessRegime, fired: bool) -> SessionFeatures:
    """Benign features; if fired, they trip the rule for regime (default config thresholds)."""
    # SessionFeatures requires computed_at (datetime); user_id/lab_slug aren't in the model
    base = dict(
        avg_inter_action_latency=5.0,
        action_rate_slope=0.0,
        idle_periods=0,
        total_active_time=10.0,
        time_on_current_step=10.0,
        error_repeat_count=0,
        error_repeat_rate=0.0,
        action_sequence_entropy=0.0,
        undo_redo_ratio=0.0,
        error_frequency=0.0,
        error_frequency_slope=0.0,
        unique_error_types=0,
        dominant_error=None,
        components_touched=1,
        action_diversity=0.5,
        events_total=ts_index + 1,
        distinct_failing_actuals=0,
        cycles_failing_unchanged=0,
        session_id="syn",
        computed_at=_EPOCH,
    )
    if fired:
        if regime == ProcessRegime.REPEATING_ERRORS:
            base.update(error_repeat_count=5, error_repeat_rate=0.6, error_frequency=0.6)
        elif regime == ProcessRegime.TRIAL_AND_ERROR:
            base.update(
                distinct_failing_actuals=5, action_sequence_entropy=0.9, error_frequency=0.6
            )
        elif regime == ProcessRegime.STUCK_ON_STEP:
            base.update(cycles_failing_unchanged=4)
        elif regime == ProcessRegime.IDLE:
            # IDLE rule: idle_periods > threshold AND action_rate_slope < rate_slope_threshold(-0.5)
            base.update(idle_periods=4, avg_inter_action_latency=120.0, action_rate_slope=-1.0)
    return SessionFeatures(**base)


def build_synthetic_scenarios() -> list["LabeledScenario"]:
    """The identifier fixture: 4 regimes x 3 onsets, plus 5 normal sessions.

    Single source for the admin dashboard, eval_identifier and the defense export;
    the three used to build it separately and drift. Detection delays and blips
    make the identifier imperfect in both directions, without which T_k selection
    is vacuous.
    """
    scns = []
    for regime in (
        ProcessRegime.REPEATING_ERRORS,
        ProcessRegime.TRIAL_AND_ERROR,
        ProcessRegime.STUCK_ON_STEP,
        ProcessRegime.IDLE,
    ):
        for onset, delay in ((4, 0), (5, 1), (6, 2)):
            scns.append(
                make_struggle_scenario(
                    regime,
                    onset_index=onset,
                    n=14,
                    step=15.0,
                    # Window must span the T_k grid, else every T_k past it is a
                    # miss by arithmetic. Lateness is reported as latency.
                    window=14 * 15.0,
                    detect_delay=delay,
                )
            )
    for blips in ((), (), (), (3, 4), (7, 8, 9)):
        scns.append(make_normal_scenario(n=14, step=15.0, blip_indices=blips))
    return scns


def build_synthetic_sessions() -> list[dict]:
    """Sessions for the T_k sweep: one bad spell of N seconds, then productive."""

    def _session(spell_len: int, regime: str = "stuck_on_step", t_step: int = 15) -> dict:
        samples: list[dict] = []
        t, dwell = 0, 0.0
        while t <= spell_len:
            samples.append({"ts": float(t), "regime": regime, "dwell": dwell})
            t += t_step
            dwell += float(t_step)
        samples.append({"ts": float(t), "regime": "productive", "dwell": 0.0})
        return {"samples": samples}

    return [_session(n) for n in (30, 30, 60, 120, 180, 300, 600)]


def make_normal_scenario(
    n: int = 12,
    step: float = 15.0,
    source: str = "synthetic",
    blip_indices: tuple[int, ...] = (),
    blip_regime: ProcessRegime = ProcessRegime.REPEATING_ERRORS,
) -> "LabeledScenario":
    """Productive session. `blip_indices` are snapshots whose features trip a rule.

    Blips are the only source of false positives here; without them c_false
    multiplies zero. Indices are explicit, not random, to keep the curve reproducible.
    """
    snaps = [
        Snapshot(i * step, _features(i, blip_regime, fired=(i in blip_indices))) for i in range(n)
    ]
    return LabeledScenario(snaps, None, 0.0, ProcessRegime.PRODUCTIVE, n * step, source)


def make_struggle_scenario(
    regime: ProcessRegime,
    onset_index: int = 6,
    n: int = 12,
    step: float = 15.0,
    window: float = 30.0,
    source: str = "synthetic",
    detect_delay: int = 0,
) -> "LabeledScenario":
    """Session that enters `regime` at `onset_index`.

    `detect_delay` keeps features benign for N snapshots after the true onset.
    At the default 0 the features flip exactly at onset: a perfect detector, so
    recall is 1.0 by construction and T_k selection is vacuous.
    """
    fire_from = onset_index + detect_delay
    snaps = [Snapshot(i * step, _features(i, regime, fired=(i >= fire_from))) for i in range(n)]
    return LabeledScenario(snaps, onset_index * step, window, regime, n * step, source)
