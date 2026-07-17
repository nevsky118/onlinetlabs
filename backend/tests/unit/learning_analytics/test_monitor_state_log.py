from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from agents.analytics.models import StruggleType
from config.config_model import LearningAnalyticsConfig
from learning_analytics.monitor import SessionMonitor
from learning_analytics.process_state import ProcessRegime

pytestmark = [pytest.mark.unit]


class _Cap:
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


class TestMonitorStateLog:
    @autotest.num("1542")
    @autotest.external_id("264681a7-5244-4ab3-8544-d7fb3f708681")
    @autotest.name("MonitorStateLog: логирует состояние на каждый цикл, dwell накапливается")
    async def test_264681a7_logs_state_every_cycle(self):
        with autotest.step("Arrange: монитор с захватывающей сессией БД"):
            cap = _Cap()
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=lambda: cap,
                orchestrator=MagicMock(),
                learning_analytics_config=LearningAnalyticsConfig(),
            )
            monitor._session_id, monitor._user_id, monitor._lab_slug = "s1", "u1", "lab-1"
            a = SimpleNamespace(struggle_detected=True, struggle_type=StruggleType.IDLE)
            t = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)

        with autotest.step("Act: два вызова _log_process_state с разрывом 15 сек"):
            r1, d1 = await monitor._log_process_state(a, t)
            r2, d2 = await monitor._log_process_state(a, t + timedelta(seconds=15))

        with autotest.step("Assert: режимы и dwell корректны, записи добавлены в БД"):
            assert_equal(r1, ProcessRegime.IDLE, "первый режим IDLE")
            assert_equal(d1, 0.0, "первый dwell 0.0")
            assert_equal(d2, 15.0, "второй dwell 15.0")
            assert_equal(len(cap.added), 2, "два объекта добавлено в сессию")
            assert_equal(cap.added[0].regime, "idle", "первая запись, режим idle")
            assert_equal(cap.added[0].dwell_seconds, 0.0, "первая запись, dwell 0.0")
