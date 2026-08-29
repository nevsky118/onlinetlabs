from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from agents.identifier.schemas import StruggleType
from analytics.runtime.monitor import SessionMonitor
from analytics.runtime.process_state import ProcessRegime
from config.config_model import LearningAnalyticsConfig
from tests.settings.data.db_data import CapturingSessionData

pytestmark = [pytest.mark.unit]


class TestMonitorStateLog:
    @autotest.num("1542")
    @autotest.external_id("264681a7-5244-4ab3-8544-d7fb3f708681")
    @autotest.name("MonitorStateLog: logs state every cycle, dwell accumulates")
    async def test_264681a7_logs_state_every_cycle(self):
        with autotest.step("Arrange: monitor with a capturing DB session"):
            cap = CapturingSessionData()
            monitor = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=lambda: cap,
                orchestrator=MagicMock(),
                learning_analytics_config=LearningAnalyticsConfig(),
            )
            monitor._session_id, monitor._user_id, monitor._lab_slug = "s1", "u1", "lab-1"
            analysis = SimpleNamespace(struggle_detected=True, struggle_type=StruggleType.IDLE)
            moment = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)

        with autotest.step("Act: two _log_process_state calls 15 sec apart"):
            r1, d1 = await monitor._log_process_state(analysis, moment)
            r2, d2 = await monitor._log_process_state(analysis, moment + timedelta(seconds=15))

        with autotest.step("Assert: regimes and dwell are correct, rows added to the DB"):
            assert_equal(r1, ProcessRegime.IDLE, "first regime is IDLE")
            assert_equal(d1, 0.0, "first dwell 0.0")
            assert_equal(d2, 15.0, "second dwell 15.0")
            assert_equal(len(cap.added), 2, "two objects added to the session")
            assert_equal(cap.added[0].regime, "idle", "first row, regime idle")
            assert_equal(cap.added[0].dwell_seconds, 0.0, "first row, dwell 0.0")
