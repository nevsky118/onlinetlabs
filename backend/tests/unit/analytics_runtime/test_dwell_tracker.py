from datetime import UTC, datetime, timedelta

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from analytics.runtime.process_state import DwellTracker, ProcessRegime

pytestmark = [pytest.mark.unit]


class TestDwellTracker:
    @autotest.num("1482")
    @autotest.external_id("42f1732e-d33f-419c-a17f-b31c923d32b3")
    @autotest.name("DwellTracker: accumulates time and resets on regime change")
    def test_42f1732e_accumulates_then_resets(self):
        with autotest.step("Arrange: tracker and a reference time point"):
            moment = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
            dt = DwellTracker()

        with autotest.step("Act: a series of observations in STUCK_ON_STEP regime"):
            obs0 = dt.observe(ProcessRegime.STUCK_ON_STEP, moment)
            obs15 = dt.observe(ProcessRegime.STUCK_ON_STEP, moment + timedelta(seconds=15))
            obs30 = dt.observe(ProcessRegime.STUCK_ON_STEP, moment + timedelta(seconds=30))
            obs_switch = dt.observe(ProcessRegime.PRODUCTIVE, moment + timedelta(seconds=45))

        with autotest.step(
            "Assert: first observation is 0, later ones accumulate, regime change resets"
        ):
            assert_equal(obs0, 0.0, "first observation is 0.0")
            assert_equal(obs15, 15.0, "after 15 sec, 15.0")
            assert_equal(obs30, 30.0, "after 30 sec, 30.0")
            assert_equal(obs_switch, 0.0, "regime change resets to 0.0")
            assert_equal(dt.current_regime, ProcessRegime.PRODUCTIVE, "current regime updated")
