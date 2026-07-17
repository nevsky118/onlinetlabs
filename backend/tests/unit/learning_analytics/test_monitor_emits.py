"""Test: SessionMonitor emits activity events when struggle is detected."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp_sdk.testing import autotest

from agents.analytics.agent import identify_regime
from agents.analytics.models import SessionFeatures
from config.config_model import LearningAnalyticsConfig
from learning_analytics.context import AgentContext
from learning_analytics.monitor import SessionMonitor
from observability.models import ActivityKind

pytestmark = [pytest.mark.unit]


def _make_struggle_features(session_id: str = "s1") -> SessionFeatures:
    """Features with error_repeat_count=4 → triggers REPEATING_ERRORS."""
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
        dominant_error="bad ip",
        components_touched=1,
        action_diversity=0.1,
        events_total=5,
    )


def _make_monitor(activity_log, config_model) -> SessionMonitor:
    """Monitor with a mocked context_builder."""
    monitor = SessionMonitor(
        mcp_client=None,
        db_factory=None,
        orchestrator=MagicMock(),
        learning_analytics_config=LearningAnalyticsConfig(),
        gateway=MagicMock(),
        activity_log=activity_log,
    )
    monitor._session_id = "s1"
    monitor._user_id = "u1"
    monitor._lab_slug = "lab-gns3"
    monitor._ctx = MagicMock()
    # Mock context_builder.build → AgentContext
    monitor._context_builder.build = AsyncMock(
        return_value=AgentContext(
            topology_summary="1 router",
            recent_errors=["bad ip", "bad ip", "bad ip", "bad ip"],
            recent_actions=["cfg_err"],
            struggle_type="repeating_errors",
            dominant_error="bad ip",
            features_summary="4 повтора ошибки",
        )
    )
    return monitor


class TestMonitorEmits:
    @autotest.num("580")
    @autotest.external_id("75ce6cbf-cfe9-4ebd-bb92-0b2fdf6f99ee")
    @autotest.name("SessionMonitor: emit STRUGGLE_DETECTED при обнаружении затруднения")
    async def test_75ce6cbf_emits_struggle_detected(self, config_model):
        # Arrange
        with autotest.step("Создаём монитор с activity_log mock и struggle-фичами"):
            activity = MagicMock()
            monitor = _make_monitor(activity, config_model)
            features = _make_struggle_features()

        # Act
        with autotest.step("Вызываем _decide_intervention с затруднением"):
            analysis = identify_regime(features, LearningAnalyticsConfig())
            result = await monitor._decide_intervention(analysis, features)

        # Assert
        with autotest.step("Проверяем, что emit был вызван с STRUGGLE_DETECTED"):
            assert activity.emit.called, "emit не вызван"
            emitted_kinds = [call.args[0].kind for call in activity.emit.call_args_list]
            assert ActivityKind.STRUGGLE_DETECTED in emitted_kinds, (
                f"STRUGGLE_DETECTED не найден, получено: {emitted_kinds}"
            )

    @autotest.num("581")
    @autotest.external_id("724254ea-7e51-4a4d-be40-da53a6c3d690")
    @autotest.name("SessionMonitor: emit COOLDOWN_SKIP когда cooldown ещё не прошёл")
    async def test_724254ea_emits_cooldown_skip(self, config_model):
        # Arrange
        with autotest.step("Создаём монитор с недавней интервенцией"):
            activity = MagicMock()
            monitor = _make_monitor(activity, config_model)
            monitor._last_intervention_at = datetime.now(tz=UTC)
            features = _make_struggle_features()

        # Act
        with autotest.step("Вызываем _decide_intervention"):
            analysis = identify_regime(features, LearningAnalyticsConfig())
            result = await monitor._decide_intervention(analysis, features)

        # Assert
        with autotest.step("Проверяем STRUGGLE_DETECTED и COOLDOWN_SKIP"):
            assert result is None, "интервенция должна быть заблокирована cooldown"
            emitted_kinds = [call.args[0].kind for call in activity.emit.call_args_list]
            assert ActivityKind.STRUGGLE_DETECTED in emitted_kinds, "нет STRUGGLE_DETECTED"
            assert ActivityKind.COOLDOWN_SKIP in emitted_kinds, "нет COOLDOWN_SKIP"

    @autotest.num("582")
    @autotest.external_id("7ac4d323-14f7-42fa-a58c-ca90594eaf17")
    @autotest.name("SessionMonitor: без activity_log emit не бросает исключение")
    async def test_7ac4d323_no_emit_without_activity_log(self, config_model):
        # Arrange
        with autotest.step("Создаём монитор без activity_log"):
            monitor = _make_monitor(None, config_model)
            features = _make_struggle_features()

        # Act & Assert
        with autotest.step("_decide_intervention не падает без activity_log"):
            # Must not raise an exception
            analysis = identify_regime(features, LearningAnalyticsConfig())
            await monitor._decide_intervention(analysis, features)
