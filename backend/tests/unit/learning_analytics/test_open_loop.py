"""Test: open-loop arm A suppresses proactive intervention, arm B dispatches it."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_not_none, assert_true

from agents.analytics.models import StruggleType
from agents.orchestrator.models import OrchestratorResponse
from config.config_model import LearningAnalyticsConfig
from experiment.assignment import ControlArm
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
    from agents.analytics.models import SessionFeatures

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
    from agents.analytics.models import DifficultyRecommendation, StudentMetrics

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
    from agents.analytics.models import AnalyticsResult, SuggestedIntervention

    return AnalyticsResult(
        struggle_detected=struggle,
        struggle_type=StruggleType.IDLE,
        confidence=0.9,
        suggested_intervention=SuggestedIntervention.HINT,
        difficulty_recommendation=_make_difficulty(),
        features=_make_features(),
    )


def _make_monitor(arm: ControlArm, cap: _Cap) -> SessionMonitor:
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
    m = SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=lambda: cap,
        orchestrator=orchestrator,
        learning_analytics_config=cfg,
        gateway=gateway,
        control_arm=arm,
    )
    m._session_id = "s1"
    m._user_id = "u1"
    m._lab_slug = "lab-gns3"
    m._ctx = MagicMock()
    m._session_model_id = None
    return m


class TestOpenLoop:
    @autotest.num("1362")
    @autotest.external_id("378372bd-17f6-430b-9bd5-01bad8a73284")
    @autotest.name("OpenLoop arm A: _log_would_intervene пишет событие would_intervene в БД")
    async def test_378372bd_open_arm_logs_would_intervene(self):
        with autotest.step("Arrange: монитор arm=OPEN, пустая cap"):
            cap = _Cap()
            m = _make_monitor(ControlArm.OPEN, cap)
            analysis = _make_analysis()

        with autotest.step("Act: вызвать _log_would_intervene"):
            await m._log_would_intervene(analysis)

        with autotest.step("Assert: orchestrator не вызван, would_intervene записан"):
            m._orchestrator.intervene.assert_not_called()
            types = [getattr(o, "event_type", None) for o in cap.added]
            assert_true("would_intervene" in types, f"would_intervene не записан; types: {types}")
            wi = next(o for o in cap.added if getattr(o, "event_type", None) == "would_intervene")
            assert_equal(wi.action, "hint", "action == hint")
            assert_equal(wi.session_id, "s1", "session_id == s1")
            assert_equal(wi.user_id, "u1", "user_id == u1")
            assert_equal(wi.extra_data["control_arm"], "open", "control_arm == open")
            assert_equal(wi.success, False, "success == False")

    @autotest.num("1363")
    @autotest.external_id("d67dd9a7-1f18-4a51-a829-9fc04519df24")
    @autotest.name("OpenLoop arm A: _run_analysis после dwell_ready → log, без dispatch")
    async def test_d67dd9a7_open_arm_run_analysis_no_dispatch(self):
        with autotest.step("Arrange: монитор arm=OPEN, фейковые аналитика и событие"):
            cap = _Cap()
            m = _make_monitor(ControlArm.OPEN, cap)
            analysis = _make_analysis()
            fake_event = SimpleNamespace(
                timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=UTC),
            )
            m._feature_extractor = MagicMock()
            m._feature_extractor.compute = MagicMock(return_value=_make_features())

        with autotest.step("Act: _run_analysis с одним событием"):
            with (
                patch.object(m, "_load_new_events", AsyncMock(return_value=[fake_event])),
                patch("learning_analytics.monitor.identify_regime", return_value=analysis),
            ):
                await m._run_analysis()

        with autotest.step("Assert: orchestrator не вызван, would_intervene записан"):
            m._orchestrator.intervene.assert_not_called()
            types = [getattr(o, "event_type", None) for o in cap.added]
            assert_true("would_intervene" in types, f"would_intervene не записан; types: {types}")

    @autotest.num("1364")
    @autotest.external_id("a4837de3-8bd9-4ffe-ae54-b256bb8049da")
    @autotest.name(
        "OpenLoop arm B: _decide_intervention + _dispatch_intervention вызывает orchestrator"
    )
    async def test_a4837de3_closed_arm_dispatches_intervention(self):
        with autotest.step("Arrange: монитор arm=CLOSED, мок контекста"):
            cap = _Cap()
            m = _make_monitor(ControlArm.CLOSED, cap)
            analysis = _make_analysis()

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

            features = MagicMock()
            features.dominant_error = None
            features.error_repeat_count = 0

        with autotest.step("Act: _decide_intervention и _dispatch_intervention"):
            pending = await m._decide_intervention(analysis, features)
            await m._dispatch_intervention(pending)

        with autotest.step("Assert: pending не None, orchestrator вызван"):
            assert_is_not_none(pending, "pending должен быть не None")
            m._orchestrator.intervene.assert_called_once()

    @autotest.num("1365")
    @autotest.external_id("1349493d-89e9-43f4-aa89-3ec2c537fc60")
    @autotest.name("OpenLoop arm A: второй вызов в cooldown не пишет would_intervene")
    async def test_1349493d_would_intervene_respects_cooldown(self):
        with autotest.step("Arrange: монитор arm=OPEN, cooldown=60с"):
            cap = _Cap()
            m = _make_monitor(ControlArm.OPEN, cap)
            m._learning_analytics_config.cooldown_period = 60
            analysis = _make_analysis()
            fake_event = SimpleNamespace(
                timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=UTC),
            )
            m._feature_extractor = MagicMock()
            m._feature_extractor.compute = MagicMock(return_value=_make_features())

        with autotest.step("Act: два вызова _run_analysis подряд"):
            with (
                patch.object(m, "_load_new_events", AsyncMock(return_value=[fake_event])),
                patch("learning_analytics.monitor.identify_regime", return_value=analysis),
            ):
                await m._run_analysis()
                await m._run_analysis()

        with autotest.step("Assert: ровно одно событие would_intervene"):
            wi_events = [
                o for o in cap.added if getattr(o, "event_type", None) == "would_intervene"
            ]
            assert_equal(
                len(wi_events), 1, f"ожидался 1 would_intervene, получено {len(wi_events)}"
            )

    @autotest.num("1366")
    @autotest.external_id("ef66a54c-9eb0-4248-9ade-84f216510e51")
    @autotest.name("OpenLoop: дефолтный control_arm=CLOSED не ломает существующее поведение")
    def test_ef66a54c_closed_arm_default(self):
        with autotest.step("Arrange: SessionMonitor без явного control_arm"):
            cfg = LearningAnalyticsConfig()
            m = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=cfg,
            )

        with autotest.step("Assert: _control_arm == CLOSED"):
            assert_equal(m._control_arm, ControlArm.CLOSED, "дефолт CLOSED")
