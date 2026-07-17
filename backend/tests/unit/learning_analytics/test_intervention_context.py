"""Тест: _decide_intervention строит контекст из observer.current_state()."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp_sdk.testing import autotest

from agents.analytics.agent import identify_regime
from agents.analytics.models import SessionFeatures
from config.config_model import LearningAnalyticsConfig
from learning_analytics.context import AgentContext
from learning_analytics.monitor import SessionMonitor

pytestmark = [pytest.mark.unit]


def _make_struggle_features(session_id: str = "s1") -> SessionFeatures:
    """4 повтора одной ошибки → REPEATING_ERRORS."""
    return SessionFeatures(
        session_id=session_id,
        computed_at=datetime.now(tz=UTC),
        avg_inter_action_latency=10.0,
        action_rate_slope=0.0,
        idle_periods=0,
        total_active_time=120.0,
        time_on_current_step=60.0,
        error_repeat_count=4,
        error_repeat_rate=0.8,
        action_sequence_entropy=0.2,
        undo_redo_ratio=0.0,
        error_frequency=0.5,
        error_frequency_slope=0.1,
        unique_error_types=1,
        dominant_error="ping failed",
        components_touched=1,
        action_diversity=0.1,
        events_total=5,
    )


def _make_observer_stub() -> MagicMock:
    """Стаб observer'а с current_state() → ProgressState-like объект."""
    state = SimpleNamespace(
        current_step_id="connectivity",
        current_step_title="Связность",
        failing_checks=[
            {
                "kind": "vpcs.ping",
                "params": {"from": "PC1", "to": "192.168.1.12"},
                "expected": {"received": ">=4"},
                "actual": {"received": 0},
            }
        ],
    )
    observer = MagicMock()
    observer.current_state.return_value = state
    return observer


def _make_monitor(observer, config_model) -> SessionMonitor:
    """Монитор с замоканным context_builder и observer'ом."""
    monitor = SessionMonitor(
        mcp_client=None,
        db_factory=None,
        orchestrator=MagicMock(),
        learning_analytics_config=LearningAnalyticsConfig(),
        activity_log=None,
        observer=observer,
    )
    monitor._session_id = "s1"
    monitor._user_id = "u1"
    monitor._lab_slug = "lab-gns3"
    monitor._ctx = MagicMock()
    monitor._context_builder.build = AsyncMock(
        return_value=AgentContext(
            topology_summary="1 router",
            recent_errors=["ping failed"] * 4,
            recent_actions=["ping"],
            struggle_type="repeating_errors",
            dominant_error="ping failed",
            features_summary="4 повтора ошибки",
        )
    )
    return monitor


class TestInterventionContextFromObserver:
    @autotest.num("590")
    @autotest.external_id("a0b1c2d3-e4f5-4060-b1c2-d3e4f5a6b7c8")
    @autotest.name("SessionMonitor: context содержит step_slug из observer")
    async def test_a0b1c2d3_step_slug_from_observer(self, config_model):
        # Arrange
        with autotest.step("Создаём монитор с observer-стабом"):
            observer = _make_observer_stub()
            monitor = _make_monitor(observer, config_model)
            features = _make_struggle_features()

        # Act
        with autotest.step("Вызываем _decide_intervention"):
            analysis = identify_regime(features, LearningAnalyticsConfig())
            pending = await monitor._decide_intervention(analysis, features)

        # Assert
        with autotest.step("step_slug == 'connectivity'"):
            assert pending is not None, "интервенция должна быть создана"
            ctx = pending.payload.context
            assert ctx["step_slug"] == "connectivity", (
                f"ожидали 'connectivity', получили {ctx['step_slug']!r}"
            )

    @autotest.num("591")
    @autotest.external_id("b1c2d3e4-f5a6-4171-c2d3-e4f5a6b7c8d9")
    @autotest.name("SessionMonitor: context содержит failing_check из observer")
    async def test_b1c2d3e4_failing_check_from_observer(self, config_model):
        # Arrange
        with autotest.step("Создаём монитор с observer-стабом"):
            observer = _make_observer_stub()
            monitor = _make_monitor(observer, config_model)
            features = _make_struggle_features()

        # Act
        with autotest.step("Вызываем _decide_intervention"):
            analysis = identify_regime(features, LearningAnalyticsConfig())
            pending = await monitor._decide_intervention(analysis, features)

        # Assert
        with autotest.step("failing_check[kind] == 'vpcs.ping'"):
            assert pending is not None, "интервенция должна быть создана"
            fc = pending.payload.context["failing_check"]
            assert fc is not None, "failing_check не должен быть None"
            assert fc["kind"] == "vpcs.ping", f"ожидали 'vpcs.ping', получили {fc['kind']!r}"

    @autotest.num("592")
    @autotest.external_id("c2d3e4f5-a6b7-4282-d3e4-f5a6b7c8d9ea")
    @autotest.name("SessionMonitor: без observer step_slug='current', failing_check=None")
    async def test_c2d3e4f5_no_observer_fallback(self, config_model):
        # Arrange
        with autotest.step("Создаём монитор без observer"):
            monitor = _make_monitor(None, config_model)
            features = _make_struggle_features()

        # Act
        with autotest.step("Вызываем _decide_intervention"):
            analysis = identify_regime(features, LearningAnalyticsConfig())
            pending = await monitor._decide_intervention(analysis, features)

        # Assert
        with autotest.step("step_slug='current', failing_check=None"):
            assert pending is not None
            ctx = pending.payload.context
            assert ctx["step_slug"] == "current", f"fallback step_slug: {ctx['step_slug']!r}"
            assert ctx["failing_check"] is None, (
                f"failing_check должен быть None: {ctx['failing_check']!r}"
            )
