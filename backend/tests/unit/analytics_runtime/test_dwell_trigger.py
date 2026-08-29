from unittest.mock import MagicMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_false, assert_true

from analytics.runtime.monitor import SessionMonitor
from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


def _monitor(thresholds):
    cfg = LearningAnalyticsConfig()
    cfg.dwell_thresholds = thresholds
    monitor = SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=MagicMock(),
        orchestrator=MagicMock(),
        learning_analytics_config=cfg,
    )
    return monitor


class TestDwellTrigger:
    @autotest.num("1512")
    @autotest.external_id("40aceb36-6ef0-4432-8931-f6d41a4e3688")
    @autotest.name("DwellTrigger: does not trigger below the threshold, triggers at it")
    def test_40aceb36_gate_below_and_at_threshold(self):
        with autotest.step("Arrange: monitor with idle=30 threshold"):
            monitor = _monitor(
                {
                    "idle": 30.0,
                    "stuck_on_step": 0.0,
                    "repeating_errors": 0.0,
                    "trial_and_error": 0.0,
                }
            )

        with autotest.step("Act + Assert: below threshold False, at threshold True"):
            assert_false(monitor._dwell_ready("idle", 15.0), "below T_k, does not trigger")
            assert_true(monitor._dwell_ready("idle", 30.0), "T_k reached, triggers")

    @autotest.num("1513")
    @autotest.external_id("0d9d65d1-08d1-486d-85fb-e526310e141b")
    @autotest.name("DwellTrigger: the good productive regime never triggers")
    def test_0d9d65d1_productive_never_triggers(self):
        with autotest.step("Arrange: monitor"):
            monitor = _monitor(
                {
                    "idle": 30.0,
                    "stuck_on_step": 0.0,
                    "repeating_errors": 0.0,
                    "trial_and_error": 0.0,
                }
            )

        with autotest.step("Act + Assert: productive with any dwell gives False"):
            assert_false(monitor._dwell_ready("productive", 999.0), "good regime, does not trigger")

    @autotest.num("1514")
    @autotest.external_id("bc05d46d-7548-4388-a1f7-ebb2f33e73a8")
    @autotest.name("DwellTrigger: T_k=0 baseline triggers immediately")
    def test_bc05d46d_zero_threshold_triggers_immediately(self):
        with autotest.step("Arrange: monitor with stuck_on_step=0 threshold"):
            monitor = _monitor(
                {
                    "idle": 30.0,
                    "stuck_on_step": 0.0,
                    "repeating_errors": 0.0,
                    "trial_and_error": 0.0,
                }
            )

        with autotest.step("Act + Assert: dwell=0 at T_k=0 gives True"):
            assert_true(
                monitor._dwell_ready("stuck_on_step", 0.0), "T_k=0 baseline → triggers immediately"
            )
