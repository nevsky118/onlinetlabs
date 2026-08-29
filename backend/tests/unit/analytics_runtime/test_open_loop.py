"""Test: open-loop arm A suppresses proactive intervention, arm B dispatches it."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_not_none, assert_true

from agents.identifier.schemas import StruggleType
from agents.orchestrator.schemas import OrchestratorResponse
from analytics.runtime.monitor import SessionMonitor
from config.config_model import LearningAnalyticsConfig
from experiment.assignment import ControlArm
from tests.settings.data.db_data import CapturingSessionData

pytestmark = [pytest.mark.unit]


def _make_features():
    from agents.identifier.schemas import SessionFeatures

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
    from agents.identifier.schemas import DifficultyRecommendation, StudentMetrics

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
    from agents.identifier.schemas import AnalyticsResult, SuggestedIntervention

    return AnalyticsResult(
        struggle_detected=struggle,
        struggle_type=StruggleType.IDLE,
        confidence=0.9,
        suggested_intervention=SuggestedIntervention.HINT,
        difficulty_recommendation=_make_difficulty(),
        features=_make_features(),
    )


def _make_monitor(arm: ControlArm, cap: CapturingSessionData) -> SessionMonitor:
    cfg = LearningAnalyticsConfig()
    cfg.dwell_thresholds = {
        "idle": 0.0,
        "stuck_on_step": 0.0,
        "repeating_errors": 0.0,
        "trial_and_error": 0.0,
    }
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
    monitor = SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=lambda: cap,
        orchestrator=orchestrator,
        learning_analytics_config=cfg,
        gateway=gateway,
        control_arm=arm,
    )
    monitor._session_id = "s1"
    monitor._user_id = "u1"
    monitor._lab_slug = "lab-gns3"
    monitor._ctx = MagicMock()
    monitor._session_model_id = None
    return monitor


class TestOpenLoop:
    @autotest.num("1362")
    @autotest.external_id("378372bd-17f6-430b-9bd5-01bad8a73284")
    @autotest.name("OpenLoop arm A: _log_would_intervene writes a would_intervene event to the DB")
    async def test_378372bd_open_arm_logs_would_intervene(self):
        with autotest.step("Arrange: monitor arm=OPEN, empty cap"):
            cap = CapturingSessionData()
            monitor = _make_monitor(ControlArm.OPEN, cap)
            analysis = _make_analysis()

        with autotest.step("Act: call _log_would_intervene"):
            await monitor._log_would_intervene(analysis, "open_arm")

        with autotest.step("Assert: orchestrator not called, would_intervene logged"):
            monitor._orchestrator.intervene.assert_not_called()
            types = [getattr(rowow_2, "event_type", None) for rowow_2 in cap.added]
            assert_true("would_intervene" in types, f"would_intervene not logged; types: {types}")
            wi = next(
                rowow_2
                for rowow_2 in cap.added
                if getattr(rowow_2, "event_type", None) == "would_intervene"
            )
            assert_equal(wi.action, "hint", "action == hint")
            assert_equal(wi.session_id, "s1", "session_id == s1")
            assert_equal(wi.extra_data["withheld_because"], "open_arm", "reason recorded")
            assert_equal(wi.user_id, "u1", "user_id == u1")
            assert_equal(wi.extra_data["control_arm"], "open", "control_arm == open")
            assert_equal(wi.success, False, "success == False")

    @autotest.num("1363")
    @autotest.external_id("d67dd9a7-1f18-4a51-a829-9fc04519df24")
    @autotest.name("OpenLoop arm A: _run_analysis after dwell_ready -> log, no dispatch")
    async def test_d67dd9a7_open_arm_run_analysis_no_dispatch(self):
        with autotest.step("Arrange: monitor arm=OPEN, fake analysis and event"):
            cap = CapturingSessionData()
            monitor = _make_monitor(ControlArm.OPEN, cap)
            analysis = _make_analysis()
            fake_event = SimpleNamespace(
                timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=UTC),
            )
            monitor._feature_extractor = MagicMock()
            monitor._feature_extractor.compute = MagicMock(return_value=_make_features())

        with autotest.step("Act: _run_analysis with one event"):
            with (
                patch.object(monitor, "_load_new_events", AsyncMock(return_value=[fake_event])),
                patch("analytics.runtime.monitor.identify_regime", return_value=analysis),
            ):
                await monitor._run_analysis()

        with autotest.step("Assert: orchestrator not called, would_intervene logged"):
            monitor._orchestrator.intervene.assert_not_called()
            types = [getattr(row, "event_type", None) for row in cap.added]
            assert_true("would_intervene" in types, f"would_intervene not logged; types: {types}")

    @autotest.num("1364")
    @autotest.external_id("a4837de3-8bd9-4ffe-ae54-b256bb8049da")
    @autotest.name(
        "OpenLoop arm B: _decide_intervention + _dispatch_intervention calls orchestrator"
    )
    async def test_a4837de3_closed_arm_dispatches_intervention(self):
        with autotest.step("Arrange: monitor arm=CLOSED, mocked context"):
            cap = CapturingSessionData()
            monitor = _make_monitor(ControlArm.CLOSED, cap)
            analysis = _make_analysis()

            from analytics.runtime.context import AgentContext

            monitor._context_builder.build = AsyncMock(
                return_value=AgentContext(
                    topology_summary="1 router",
                    recent_errors=[],
                    recent_actions=[],
                    struggle_type="idle",
                    dominant_error=None,
                    features_summary="",
                )
            )

            features = MagicMock()
            features.dominant_error = None
            features.error_repeat_count = 0

        with autotest.step("Act: _decide_intervention and _dispatch_intervention"):
            pending = await monitor._decide_intervention(analysis, features)
            await monitor._dispatch_intervention(pending)

        with autotest.step("Assert: pending is not None, orchestrator called"):
            assert_is_not_none(pending, "pending must not be None")
            monitor._orchestrator.intervene.assert_called_once()

    @autotest.num("1365")
    @autotest.external_id("1349493d-89e9-43f4-aa89-3ec2c537fc60")
    @autotest.name("OpenLoop arm A: second call within cooldown does not write would_intervene")
    async def test_1349493d_would_intervene_respects_cooldown(self):
        with autotest.step("Arrange: monitor arm=OPEN, cooldown=60s"):
            cap = CapturingSessionData()
            monitor = _make_monitor(ControlArm.OPEN, cap)
            monitor._learning_analytics_config.cooldown_period = 60
            analysis = _make_analysis()
            fake_event = SimpleNamespace(
                timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=UTC),
            )
            monitor._feature_extractor = MagicMock()
            monitor._feature_extractor.compute = MagicMock(return_value=_make_features())

        with autotest.step("Act: two consecutive calls to _run_analysis"):
            with (
                patch.object(monitor, "_load_new_events", AsyncMock(return_value=[fake_event])),
                patch("analytics.runtime.monitor.identify_regime", return_value=analysis),
            ):
                await monitor._run_analysis()
                await monitor._run_analysis()

        with autotest.step("Assert: exactly one would_intervene event"):
            wi_events = [
                row for row in cap.added if getattr(row, "event_type", None) == "would_intervene"
            ]
            assert_equal(len(wi_events), 1, f"expected 1 would_intervene, got {len(wi_events)}")

    @autotest.num("1366")
    @autotest.external_id("ef66a54c-9eb0-4248-9ade-84f216510e51")
    @autotest.name("OpenLoop: default control_arm=CLOSED does not break existing behavior")
    def test_ef66a54c_closed_arm_default(self):
        with autotest.step("Arrange: SessionMonitor without an explicit control_arm"):
            cfg = LearningAnalyticsConfig()
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=cfg,
            )

        with autotest.step("Assert: _control_arm == CLOSED"):
            assert_equal(monitor._control_arm, ControlArm.CLOSED, "default CLOSED")
