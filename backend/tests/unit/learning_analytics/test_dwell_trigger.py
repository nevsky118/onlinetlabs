import pytest
from unittest.mock import MagicMock

from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_true, assert_false

from config.config_model import LearningAnalyticsConfig
from learning_analytics.monitor import SessionMonitor

pytestmark = [pytest.mark.unit]


def _monitor(thresholds):
    cfg = LearningAnalyticsConfig()
    cfg.dwell_thresholds = thresholds
    m = SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=MagicMock(),
        orchestrator=MagicMock(),
        learning_analytics_config=cfg,
    )
    return m


class TestDwellTrigger:
    @autotest.num("1512")
    @autotest.external_id("40aceb36-6ef0-4432-8931-f6d41a4e3688")
    @autotest.name("DwellTrigger: не триггерит ниже порога, триггерит на пороге")
    def test_40aceb36_gate_below_and_at_threshold(self):
        with autotest.step("Arrange: монитор с порогом idle=30"):
            m = _monitor(
                {
                    "idle": 30.0,
                    "stuck_on_step": 0.0,
                    "repeating_errors": 0.0,
                    "trial_and_error": 0.0,
                }
            )

        with autotest.step("Act + Assert: ниже порога — False; на пороге — True"):
            assert_false(m._dwell_ready("idle", 15.0), "ниже T_k — не триггерим")
            assert_true(m._dwell_ready("idle", 30.0), "достигнут T_k — триггерим")

    @autotest.num("1513")
    @autotest.external_id("0d9d65d1-08d1-486d-85fb-e526310e141b")
    @autotest.name("DwellTrigger: хороший режим productive никогда не триггерит")
    def test_0d9d65d1_productive_never_triggers(self):
        with autotest.step("Arrange: монитор"):
            m = _monitor(
                {
                    "idle": 30.0,
                    "stuck_on_step": 0.0,
                    "repeating_errors": 0.0,
                    "trial_and_error": 0.0,
                }
            )

        with autotest.step("Act + Assert: productive с любым dwell — False"):
            assert_false(m._dwell_ready("productive", 999.0), "хороший режим — не триггерим")

    @autotest.num("1514")
    @autotest.external_id("bc05d46d-7548-4388-a1f7-ebb2f33e73a8")
    @autotest.name("DwellTrigger: T_k=0 baseline — триггерит немедленно")
    def test_bc05d46d_zero_threshold_triggers_immediately(self):
        with autotest.step("Arrange: монитор с порогом stuck_on_step=0"):
            m = _monitor(
                {
                    "idle": 30.0,
                    "stuck_on_step": 0.0,
                    "repeating_errors": 0.0,
                    "trial_and_error": 0.0,
                }
            )

        with autotest.step("Act + Assert: dwell=0 при T_k=0 — True"):
            assert_true(m._dwell_ready("stuck_on_step", 0.0), "T_k=0 baseline → сразу триггерим")
