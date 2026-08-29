from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.orchestrator.schemas import OrchestratorResponse
from analytics.runtime.monitor import SessionMonitor
from config.config_model import LearningAnalyticsConfig
from i18n import t
from tests.settings.data.db_data import (
    CapturingSessionData,
    MutableRowDbSessionData,
    SessionLocaleRowData,
)

pytestmark = [pytest.mark.unit]


class TestSessionMonitor:
    @autotest.num("540")
    @autotest.external_id("78b9c0d1-e2f3-4a4b-8c5d-7e8f9a0b1c2d")
    @autotest.name("SessionMonitor: initialization")
    def test_78b9c0d1_init(self):
        # Arrange
        # Act
        with autotest.step("Create a SessionMonitor"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=LearningAnalyticsConfig(),
            )

        # Assert
        with autotest.step("Check the initial state"):
            assert_true(monitor._running is False, "not running")

    @autotest.num("541")
    @autotest.external_id("89c0d1e2-f3a4-4b5c-9d6e-8f9a0b1c2d3e")
    @autotest.name("SessionMonitor: first intervention is allowed")
    def test_89c0d1e2_should_intervene_first_time(self):
        # Arrange
        with autotest.step("Create a monitor with no prior interventions"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=LearningAnalyticsConfig(),
            )

        # Act
        # Assert
        with autotest.step("Check it is allowed"):
            assert_true(
                monitor._should_trigger_intervention(),
                "first intervention is allowed",
            )

    @autotest.num("542")
    @autotest.external_id("9ad1e2f3-a4b5-4c6d-8e7f-9a0b1c2d3e4f")
    @autotest.name("SessionMonitor: cooldown blocks a repeat intervention")
    def test_9ad1e2f3_should_intervene_respects_cooldown(self):
        # Arrange
        with autotest.step("Create a monitor with a recent intervention"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=LearningAnalyticsConfig(cooldown_period=60.0),
            )
            monitor._last_intervention_at = datetime.now(tz=UTC)

        # Act
        # Assert
        with autotest.step("Check it is blocked"):
            assert_true(not monitor._should_trigger_intervention(), "cooldown blocks it")

    @autotest.num("543")
    @autotest.external_id("ab0e2f3a-b5c6-4d7e-9f8a-0b1c2d3e4f5a")
    @autotest.name("SessionMonitor: enabled=False blocks interventions")
    def test_ab0e2f3a_disabled_config_blocks_intervention(self):
        # Arrange
        with autotest.step("Create a monitor with enabled=False"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=LearningAnalyticsConfig(enabled=False),
            )

        # Act
        # Assert
        with autotest.step("Check it is blocked"):
            assert_true(not monitor._should_trigger_intervention(), "disabled blocks it")

    @autotest.num("544")
    @autotest.external_id("bc1f3a4b-c6d7-4e8f-8a9b-1c2d3e4f5a6b")
    @autotest.name("SessionMonitor: enabled=True allows interventions")
    def test_bc1f3a4b_enabled_config_allows_intervention(self):
        # Arrange
        with autotest.step("Create a monitor with enabled=True"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=LearningAnalyticsConfig(enabled=True),
            )

        # Act
        # Assert
        with autotest.step("Check it is allowed"):
            assert_true(monitor._should_trigger_intervention(), "enabled allows it")

    @autotest.num("545")
    @autotest.external_id("f6370a44-284a-4005-b9a7-49db179c694c")
    @autotest.name("SessionMonitor: logs experiment backend metadata")
    async def test_f6370a44_log_intervention_backend_metadata(self):
        # Arrange
        with autotest.step("Prepare the monitor and response metadata"):
            db_session = CapturingSessionData()
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=lambda: db_session,
                orchestrator=MagicMock(),
                learning_analytics_config=LearningAnalyticsConfig(),
            )
            monitor._session_id = "s1"
            monitor._user_id = "u1"
            monitor._lab_slug = "lab-1"
            analysis = SimpleNamespace(
                suggested_intervention=SimpleNamespace(value="hint"),
                struggle_type=SimpleNamespace(value="repeating_errors"),
                confidence=0.8,
            )
            response = OrchestratorResponse(
                agent_used="tutor",
                agent_backend="tutor",
                success=False,
                error="agent_timeout: timeout",
                latency_ms=250,
                metadata={
                    "experiment_group": "unknown",
                    "error_code": "agent_timeout",
                    "model": "tutor",
                    "provider": "tutor",
                },
            )

        # Act
        with autotest.step("Log the intervention"):
            await monitor._log_intervention_in(db_session, analysis, response)

        # Assert
        with autotest.step("Check the event metadata"):
            event = db_session.added[0]
            assert_equal(event.extra_data["experiment_group"], "unknown", "group")
            assert_equal(event.extra_data["agent_backend"], "tutor", "backend")
            assert_equal(event.extra_data["latency_ms"], 250, "latency")
            assert_equal(event.extra_data["error_code"], "agent_timeout", "error")
            assert_equal(event.message, "agent_timeout: timeout", "message")

    @autotest.num("3141")
    @autotest.external_id("73d4cdd1-5c79-4986-9291-f91515d0c67a")
    @autotest.name("SessionMonitor: intervention reads locale live, not the value cached at start")
    async def test_73d4cdd1_intervention_uses_current_locale(self):
        # Arrange
        with autotest.step(
            "Start a monitor on an English session, then flip the stored locale to Russian"
        ):
            row_holder = {"row": SessionLocaleRowData("en")}
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=lambda: MutableRowDbSessionData(row_holder),
                orchestrator=MagicMock(),
                learning_analytics_config=LearningAnalyticsConfig(),
            )
            monitor._session_id = "s1"
            monitor._user_id = "u1"
            monitor._lab_slug = "lab-1"
            monitor._ctx = MagicMock()
            monitor._context_builder = SimpleNamespace(
                build=AsyncMock(return_value=SimpleNamespace(model_dump=lambda: {}))
            )
            row_holder["row"] = SessionLocaleRowData("ru")
            analysis = SimpleNamespace(
                struggle_detected=True,
                struggle_type=SimpleNamespace(value="stuck_on_step"),
                suggested_intervention=SimpleNamespace(value="hint"),
                confidence=0.9,
            )
            features = SimpleNamespace(dominant_error=None, error_repeat_count=1)

        # Act
        with autotest.step("Build the intervention payload"):
            pending = await monitor._decide_intervention(analysis, features)

        # Assert
        with autotest.step(
            "Payload locale and question are Russian, not the English value cached at session start"
        ):
            assert_equal(pending.payload.locale, "ru", "payload locale")
            assert_equal(
                pending.payload.context["question"],
                t("prompt.struggle.stuck_on_step", "ru"),
                "question language",
            )
