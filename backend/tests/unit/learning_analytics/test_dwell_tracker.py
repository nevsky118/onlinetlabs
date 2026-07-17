from datetime import UTC, datetime, timedelta

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from learning_analytics.process_state import DwellTracker, ProcessRegime

pytestmark = [pytest.mark.unit]


class TestDwellTracker:
    @autotest.num("1482")
    @autotest.external_id("42f1732e-d33f-419c-a17f-b31c923d32b3")
    @autotest.name("DwellTracker: накапливает время и сбрасывается при смене режима")
    def test_42f1732e_accumulates_then_resets(self):
        with autotest.step("Arrange: трекер и опорная точка времени"):
            t = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
            dt = DwellTracker()

        with autotest.step("Act: серия наблюдений в режиме STUCK_ON_STEP"):
            obs0 = dt.observe(ProcessRegime.STUCK_ON_STEP, t)
            obs15 = dt.observe(ProcessRegime.STUCK_ON_STEP, t + timedelta(seconds=15))
            obs30 = dt.observe(ProcessRegime.STUCK_ON_STEP, t + timedelta(seconds=30))
            obs_switch = dt.observe(ProcessRegime.PRODUCTIVE, t + timedelta(seconds=45))

        with autotest.step(
            "Assert: первое наблюдение — 0; последующие накапливают; смена режима сбрасывает"
        ):
            assert_equal(obs0, 0.0, "первое наблюдение — 0.0")
            assert_equal(obs15, 15.0, "через 15 сек — 15.0")
            assert_equal(obs30, 30.0, "через 30 сек — 30.0")
            assert_equal(obs_switch, 0.0, "смена режима сбрасывает до 0.0")
            assert_equal(dt.current_regime, ProcessRegime.PRODUCTIVE, "текущий режим обновлён")
