import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from learning_analytics.monitor import SessionMonitor
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_true

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


class TestSessionMonitor:
    @autotest.num("540")
    @autotest.external_id("78b9c0d1-e2f3-4a4b-8c5d-7e8f9a0b1c2d")
    @autotest.name("SessionMonitor: инициализация")
    def test_78b9c0d1_init(self):
        with autotest.step("Создаём SessionMonitor"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(), db_factory=MagicMock(),
                orchestrator=MagicMock(), learning_analytics_config=FakeLearningAnalyticsConfig(),
            )

        with autotest.step("Проверяем начальное состояние"):
            assert_true(monitor._running is False, "не запущен")

    @autotest.num("541")
    @autotest.external_id("89c0d1e2-f3a4-4b5c-9d6e-8f9a0b1c2d3e")
    @autotest.name("SessionMonitor: первая интервенция разрешена")
    def test_89c0d1e2_should_intervene_first_time(self):
        with autotest.step("Создаём монитор без предыдущих интервенций"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(), db_factory=MagicMock(),
                orchestrator=MagicMock(), learning_analytics_config=FakeLearningAnalyticsConfig(),
            )

        with autotest.step("Проверяем разрешение"):
            assert_true(monitor._should_intervene(), "первая интервенция разрешена")

    @autotest.num("542")
    @autotest.external_id("9ad1e2f3-a4b5-4c6d-8e7f-9a0b1c2d3e4f")
    @autotest.name("SessionMonitor: cooldown блокирует повторную интервенцию")
    def test_9ad1e2f3_should_intervene_respects_cooldown(self):
        with autotest.step("Создаём монитор с недавней интервенцией"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(), db_factory=MagicMock(),
                orchestrator=MagicMock(), learning_analytics_config=FakeLearningAnalyticsConfig(cooldown_period=60.0),
            )
            monitor._last_intervention_at = datetime.now(tz=timezone.utc)

        with autotest.step("Проверяем блокировку"):
            assert_true(not monitor._should_intervene(), "cooldown блокирует")

    @autotest.num("543")
    @autotest.external_id("ab0e2f3a-b5c6-4d7e-9f8a-0b1c2d3e4f5a")
    @autotest.name("SessionMonitor: enabled=False блокирует интервенции")
    def test_ab0e2f3a_disabled_config_blocks_intervention(self):
        with autotest.step("Создаём монитор с enabled=False"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(), db_factory=MagicMock(),
                orchestrator=MagicMock(), learning_analytics_config=FakeLearningAnalyticsConfig(enabled=False),
            )

        with autotest.step("Проверяем блокировку"):
            assert_true(not monitor._should_trigger_intervention(), "disabled блокирует")

    @autotest.num("544")
    @autotest.external_id("bc1f3a4b-c6d7-4e8f-8a9b-1c2d3e4f5a6b")
    @autotest.name("SessionMonitor: enabled=True разрешает интервенции")
    def test_bc1f3a4b_enabled_config_allows_intervention(self):
        with autotest.step("Создаём монитор с enabled=True"):
            monitor = SessionMonitor(
                mcp_client=MagicMock(), db_factory=MagicMock(),
                orchestrator=MagicMock(), learning_analytics_config=FakeLearningAnalyticsConfig(enabled=True),
            )

        with autotest.step("Проверяем разрешение"):
            assert_true(monitor._should_trigger_intervention(), "enabled разрешает")
