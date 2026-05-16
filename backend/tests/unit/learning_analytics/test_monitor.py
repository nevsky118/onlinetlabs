import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from agents.orchestrator.models import OrchestratorResponse
from learning_analytics.monitor import SessionMonitor
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class FakeLearningAnalyticsConfig:
    def __init__(self, **kwargs):
        self.poll_interval = kwargs.get("poll_interval", 1.0)
        self.analysis_interval = kwargs.get("analysis_interval", 2.0)
        self.cooldown_period = kwargs.get("cooldown_period", 60.0)
        self.enabled = kwargs.get("enabled", True)
        self.error_repeat_threshold = kwargs.get("error_repeat_threshold", 3)
        self.idle_threshold = kwargs.get("idle_threshold", 3)
        self.entropy_threshold = kwargs.get("entropy_threshold", 0.9)
        self.error_freq_threshold = kwargs.get("error_freq_threshold", 2.0)
        self.stuck_time_multiplier = kwargs.get("stuck_time_multiplier", 2.0)


class CapturingSession:
    def __init__(self):
        self.added = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        return None


class TestSessionMonitor:
    @autotest.num("540")
    @autotest.external_id("78b9c0d1-e2f3-4a4b-8c5d-7e8f9a0b1c2d")
    @autotest.name("SessionMonitor: инициализация")
    def test_78b9c0d1_init(self):
        # Arrange
        # Act
        with autotest.step("Создаём SessionMonitor"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=FakeLearningAnalyticsConfig(),
            )

        # Assert
        with autotest.step("Проверяем начальное состояние"):
            assert_true(monitor._running is False, "не запущен")

    @autotest.num("541")
    @autotest.external_id("89c0d1e2-f3a4-4b5c-9d6e-8f9a0b1c2d3e")
    @autotest.name("SessionMonitor: первая интервенция разрешена")
    def test_89c0d1e2_should_intervene_first_time(self):
        # Arrange
        with autotest.step("Создаём монитор без предыдущих интервенций"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=FakeLearningAnalyticsConfig(),
            )

        # Act
        # Assert
        with autotest.step("Проверяем разрешение"):
            assert_true(monitor._should_intervene(), "первая интервенция разрешена")

    @autotest.num("542")
    @autotest.external_id("9ad1e2f3-a4b5-4c6d-8e7f-9a0b1c2d3e4f")
    @autotest.name("SessionMonitor: cooldown блокирует повторную интервенцию")
    def test_9ad1e2f3_should_intervene_respects_cooldown(self):
        # Arrange
        with autotest.step("Создаём монитор с недавней интервенцией"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=FakeLearningAnalyticsConfig(
                    cooldown_period=60.0
                ),
            )
            monitor._last_intervention_at = datetime.now(tz=timezone.utc)

        # Act
        # Assert
        with autotest.step("Проверяем блокировку"):
            assert_true(not monitor._should_intervene(), "cooldown блокирует")

    @autotest.num("543")
    @autotest.external_id("ab0e2f3a-b5c6-4d7e-9f8a-0b1c2d3e4f5a")
    @autotest.name("SessionMonitor: enabled=False блокирует интервенции")
    def test_ab0e2f3a_disabled_config_blocks_intervention(self):
        # Arrange
        with autotest.step("Создаём монитор с enabled=False"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=FakeLearningAnalyticsConfig(enabled=False),
            )

        # Act
        # Assert
        with autotest.step("Проверяем блокировку"):
            assert_true(
                not monitor._should_trigger_intervention(), "disabled блокирует"
            )

    @autotest.num("544")
    @autotest.external_id("bc1f3a4b-c6d7-4e8f-8a9b-1c2d3e4f5a6b")
    @autotest.name("SessionMonitor: enabled=True разрешает интервенции")
    def test_bc1f3a4b_enabled_config_allows_intervention(self):
        # Arrange
        with autotest.step("Создаём монитор с enabled=True"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=MagicMock(),
                orchestrator=MagicMock(),
                learning_analytics_config=FakeLearningAnalyticsConfig(enabled=True),
            )

        # Act
        # Assert
        with autotest.step("Проверяем разрешение"):
            assert_true(monitor._should_trigger_intervention(), "enabled разрешает")

    @autotest.num("545")
    @autotest.external_id("f6370a44-284a-4005-b9a7-49db179c694c")
    @autotest.name("SessionMonitor: логирует experiment backend metadata")
    async def test_f6370a44_log_intervention_backend_metadata(self):
        # Arrange
        with autotest.step("Готовим монитор и response metadata"):
            db_session = CapturingSession()
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=lambda: db_session,
                orchestrator=MagicMock(),
                learning_analytics_config=FakeLearningAnalyticsConfig(),
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
                agent_used="openclaw",
                agent_backend="openclaw",
                success=False,
                error="openclaw_timeout: timeout",
                latency_ms=250,
                metadata={
                    "experiment_group": "group_b",
                    "error_code": "openclaw_timeout",
                    "model": "openclaw",
                    "provider": "openclaw",
                },
            )

        # Act
        with autotest.step("Логируем интервенцию"):
            await monitor._log_intervention(analysis, response)

        # Assert
        with autotest.step("Проверяем metadata события"):
            event = db_session.added[0]
            assert_equal(event.extra_data["experiment_group"], "group_b", "group")
            assert_equal(event.extra_data["agent_backend"], "openclaw", "backend")
            assert_equal(event.extra_data["latency_ms"], 250, "latency")
            assert_equal(event.extra_data["error_code"], "openclaw_timeout", "error")
            assert_equal(event.message, "openclaw_timeout: timeout", "message")
