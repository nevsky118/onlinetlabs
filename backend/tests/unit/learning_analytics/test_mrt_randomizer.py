"""MRT: per-decision-point randomization of intervene/withhold + decision-point logging."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.identifier.models import StruggleType
from agents.orchestrator.models import OrchestratorResponse
from config.config_model import LearningAnalyticsConfig
from learning_analytics.monitor import SessionMonitor

pytestmark = [pytest.mark.unit]


class _Cap:
    """Capturing db session."""

    def __init__(self):
        self.added = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass

    async def execute(self, stmt):
        return _ScalarResult(None)

    async def get(self, model, key):
        return None


class _ScalarResult:
    def __init__(self, v):
        self._v = v

    def scalar_one_or_none(self):
        return self._v

    def scalars(self):
        return self

    def all(self):
        return []


def _make_features():
    from agents.identifier.models import SessionFeatures

    return SessionFeatures(
        session_id="s1",
        computed_at=datetime(2026, 6, 21, 12, 0, tzinfo=UTC),
        avg_inter_action_latency=10.0,
        action_rate_slope=0.0,
        idle_periods=1,
        total_active_time=120.0,
        time_on_current_step=60.0,
        error_repeat_count=2,
        error_repeat_rate=0.5,
        action_sequence_entropy=0.3,
        undo_redo_ratio=0.0,
        error_frequency=0.3,
        error_frequency_slope=0.0,
        unique_error_types=1,
        dominant_error=None,
        components_touched=1,
        action_diversity=0.2,
        events_total=10,
    )


def _make_difficulty():
    from agents.identifier.models import DifficultyRecommendation, StudentMetrics

    return DifficultyRecommendation(
        current_difficulty="beginner",
        recommended_difficulty="beginner",
        reasoning="ok",
        metrics=StudentMetrics(
            total_attempts=5,
            success_rate=0.6,
            avg_time_per_step=30.0,
            struggling_steps=[],
        ),
    )


def _make_analysis(*, struggle=True):
    from agents.identifier.models import AnalyticsResult, SuggestedIntervention

    return AnalyticsResult(
        struggle_detected=struggle,
        struggle_type=StruggleType.IDLE,
        confidence=0.9,
        suggested_intervention=SuggestedIntervention.HINT,
        difficulty_recommendation=_make_difficulty(),
        features=_make_features(),
    )


def _make_monitor(cap, *, mrt_enabled, hold_prob=0.5, jitter=0.5, dwell_thresholds=None):
    cfg = LearningAnalyticsConfig()
    cfg.dwell_thresholds = dwell_thresholds or {
        "idle": 0.0,
        "stuck_on_step": 0.0,
        "repeating_errors": 0.0,
        "trial_and_error": 0.0,
    }
    cfg.mrt_enabled = mrt_enabled
    cfg.mrt_hold_probability = hold_prob
    cfg.mrt_t_k_jitter_frac = jitter
    orchestrator = MagicMock()
    orchestrator.intervene = AsyncMock(
        return_value=OrchestratorResponse(
            success=True,
            agent_used="tutor",
            agent_backend="openrouter",
            data={"hint": "test hint", "hint_level": 1},
            metadata={"model": "m"},
            error=None,
            latency_ms=10,
        )
    )
    gateway = MagicMock()
    gateway.send_intervention = AsyncMock()
    m = SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=lambda: cap,
        orchestrator=orchestrator,
        learning_analytics_config=cfg,
        gateway=gateway,
    )
    m._session_id = "s1"
    m._user_id = "u1"
    m._lab_slug = "lab-gns3"
    m._ctx = MagicMock()
    m._session_model_id = None
    m._feature_extractor = MagicMock()
    m._feature_extractor.compute = MagicMock(return_value=_make_features())
    from learning_analytics.context import AgentContext

    m._context_builder.build = AsyncMock(
        return_value=AgentContext(
            topology_summary="1 router",
            recent_errors=[],
            recent_actions=[],
            struggle_type="idle",
            dominant_error=None,
            features_summary="",
        )
    )
    return m


def _fake_event():
    return SimpleNamespace(timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=UTC))


def _decisions(cap):
    return [o for o in cap.added if type(o).__name__ == "InterventionDecision"]


class TestMRTRandomizer:
    @autotest.num("1969")
    @autotest.external_id("69d64974-b2d4-4cac-9ee6-5e18f3481ab9")
    @autotest.name("MRT: _mrt_open_spell sets a jittered T_k in [base*(1-f), base*(1+f)]")
    def test_69d64974_spell_jitter_within_range(self):
        with autotest.step("Arrange: monitor, dwell_thresholds[idle]=100, jitter=0.5"):
            cap = _Cap()
            m = _make_monitor(cap, mrt_enabled=True, jitter=0.5, dwell_thresholds={"idle": 100.0})

        with autotest.step("Act: open the idle spell 50 times"):
            samples = []
            for _ in range(50):
                m._mrt_open_spell("idle")
                samples.append(m._spell_t_k)

        with autotest.step("Assert: spell_id is set, all T_k in [50,150]"):
            assert_true(m._spell_id is not None, "spell_id is set")
            assert_true(
                all(50.0 <= t <= 150.0 for t in samples),
                f"all T_k in [50,150]; min={min(samples)}, max={max(samples)}",
            )

    @autotest.num("1970")
    @autotest.external_id("725a54f1-11fe-4057-9c7e-70926ccadeb4")
    @autotest.name(
        "MRT: withhold (hold=1.0) writes InterventionDecision assignment=withhold, no dispatch"
    )
    async def test_725a54f1_withhold_records_decision_no_dispatch(self):
        with autotest.step("Arrange: MRT monitor, hold_probability=1.0 (always withhold)"):
            cap = _Cap()
            m = _make_monitor(cap, mrt_enabled=True, hold_prob=1.0)

        with autotest.step("Act: _run_analysis with one event"):
            with (
                patch.object(m, "_load_new_events", AsyncMock(return_value=[_fake_event()])),
                patch(
                    "learning_analytics.monitor.identify_regime",
                    return_value=_make_analysis(),
                ),
            ):
                await m._run_analysis()

        with autotest.step("Assert: withhold decision point recorded, orchestrator not called"):
            decisions = _decisions(cap)
            assert_equal(len(decisions), 1, f"exactly 1 decision point; got {len(decisions)}")
            assert_equal(decisions[0].assignment, "withhold", "assignment == withhold")
            assert_equal(decisions[0].session_id, "s1", "session_id passed through")
            assert_true(decisions[0].spell_id is not None, "spell_id is set")
            m._orchestrator.intervene.assert_not_called()
            types = [getattr(o, "event_type", None) for o in cap.added]
            assert_true("would_intervene" in types, f"would_intervene recorded; types {types}")

    @autotest.num("1971")
    @autotest.external_id("238f96be-f346-42d0-aece-f25a3a62eb64")
    @autotest.name("MRT: intervene (hold=0.0) writes assignment=intervene and dispatches")
    async def test_238f96be_intervene_records_and_dispatches(self):
        with autotest.step("Arrange: MRT monitor, hold_probability=0.0 (always intervene)"):
            cap = _Cap()
            m = _make_monitor(cap, mrt_enabled=True, hold_prob=0.0)

        with autotest.step("Act: _run_analysis with one event"):
            with (
                patch.object(m, "_load_new_events", AsyncMock(return_value=[_fake_event()])),
                patch(
                    "learning_analytics.monitor.identify_regime",
                    return_value=_make_analysis(),
                ),
            ):
                await m._run_analysis()

        with autotest.step("Assert: intervene decision point, orchestrator called"):
            decisions = _decisions(cap)
            assert_equal(len(decisions), 1, f"exactly 1 decision point; got {len(decisions)}")
            assert_equal(decisions[0].assignment, "intervene", "assignment == intervene")
            m._orchestrator.intervene.assert_called_once()

    @autotest.num("1972")
    @autotest.external_id("7e0b9735-e4da-4371-8bd9-9a9a279b53ad")
    @autotest.name("MRT off: decision points are NOT written (behavior unchanged)")
    async def test_7e0b9735_mrt_off_no_decisions(self):
        with autotest.step("Arrange: monitor with mrt_enabled=False (default)"):
            cap = _Cap()
            m = _make_monitor(cap, mrt_enabled=False)

        with autotest.step("Act: _run_analysis with one event"):
            with (
                patch.object(m, "_load_new_events", AsyncMock(return_value=[_fake_event()])),
                patch(
                    "learning_analytics.monitor.identify_regime",
                    return_value=_make_analysis(),
                ),
            ):
                await m._run_analysis()

        with autotest.step("Assert: no InterventionDecision at all"):
            assert_equal(len(_decisions(cap)), 0, "MRT disabled → no decision points")
