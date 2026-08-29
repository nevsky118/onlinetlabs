from unittest.mock import MagicMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_false, assert_true

from analytics.runtime.monitor import SessionMonitor
from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


def _make_monitor(escalation_max_dwell=180.0):
    cfg = LearningAnalyticsConfig(escalation_max_dwell=escalation_max_dwell)
    return SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=MagicMock(),
        orchestrator=MagicMock(),
        learning_analytics_config=cfg,
    )


class TestObjectiveEscalation:
    @autotest.num("1332")
    @autotest.external_id("0c142868-1ac4-46c9-a9bf-b310e44c4bcb")
    @autotest.name("SessionMonitor._is_escalation: below threshold -> False")
    def test_0c142868_below_threshold(self):
        with autotest.step("Arrange: monitor with a 180s threshold"):
            monitor = _make_monitor(escalation_max_dwell=180.0)
        with autotest.step("Act: check dwell=120"):
            result = monitor._is_escalation(120.0)
        with autotest.step("Assert: result is False"):
            assert_false(result, "120 < 180 -> not an escalation")

    @autotest.num("1333")
    @autotest.external_id("67c4b0d9-1cca-419a-beb8-01eb809c7d76")
    @autotest.name("SessionMonitor._is_escalation: exactly at threshold -> True")
    def test_67c4b0d9_at_threshold(self):
        with autotest.step("Arrange: monitor with a 180s threshold"):
            monitor = _make_monitor(escalation_max_dwell=180.0)
        with autotest.step("Act: check dwell=180"):
            result = monitor._is_escalation(180.0)
        with autotest.step("Assert: result is True"):
            assert_true(result, "180 == 180 -> escalation")

    @autotest.num("1334")
    @autotest.external_id("7e9a6ff3-98e3-42de-b1d0-aeb9b158c011")
    @autotest.name("SessionMonitor._is_escalation: above threshold -> True")
    def test_7e9a6ff3_above_threshold(self):
        with autotest.step("Arrange: monitor with a 180s threshold"):
            monitor = _make_monitor(escalation_max_dwell=180.0)
        with autotest.step("Act: check dwell=300"):
            result = monitor._is_escalation(300.0)
        with autotest.step("Assert: result is True"):
            assert_true(result, "300 > 180 -> escalation")

    @autotest.num("1335")
    @autotest.external_id("87913e06-fcda-42a9-9423-b4228d04cd71")
    @autotest.name("SessionMonitor._escalated_in_spell: initial value is False")
    def test_87913e06_escalated_in_spell_initialized_false(self):
        with autotest.step("Arrange: default monitor"):
            monitor = _make_monitor()
        with autotest.step("Assert: _escalated_in_spell == False"):
            assert_false(monitor._escalated_in_spell, "_escalated_in_spell must be False on init")
