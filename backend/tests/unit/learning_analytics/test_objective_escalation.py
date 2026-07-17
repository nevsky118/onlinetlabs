from unittest.mock import MagicMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_false, assert_true

from config.config_model import LearningAnalyticsConfig
from learning_analytics.monitor import SessionMonitor

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
    @autotest.name("SessionMonitor._is_escalation: ниже порога → False")
    def test_0c142868_below_threshold(self):
        with autotest.step("Arrange: монитор с порогом 180с"):
            m = _make_monitor(escalation_max_dwell=180.0)
        with autotest.step("Act: проверить dwell=120"):
            result = m._is_escalation(120.0)
        with autotest.step("Assert: результат False"):
            assert_false(result, "120 < 180 → не эскалация")

    @autotest.num("1333")
    @autotest.external_id("67c4b0d9-1cca-419a-beb8-01eb809c7d76")
    @autotest.name("SessionMonitor._is_escalation: ровно на пороге → True")
    def test_67c4b0d9_at_threshold(self):
        with autotest.step("Arrange: монитор с порогом 180с"):
            m = _make_monitor(escalation_max_dwell=180.0)
        with autotest.step("Act: проверить dwell=180"):
            result = m._is_escalation(180.0)
        with autotest.step("Assert: результат True"):
            assert_true(result, "180 == 180 → эскалация")

    @autotest.num("1334")
    @autotest.external_id("7e9a6ff3-98e3-42de-b1d0-aeb9b158c011")
    @autotest.name("SessionMonitor._is_escalation: выше порога → True")
    def test_7e9a6ff3_above_threshold(self):
        with autotest.step("Arrange: монитор с порогом 180с"):
            m = _make_monitor(escalation_max_dwell=180.0)
        with autotest.step("Act: проверить dwell=300"):
            result = m._is_escalation(300.0)
        with autotest.step("Assert: результат True"):
            assert_true(result, "300 > 180 → эскалация")

    @autotest.num("1335")
    @autotest.external_id("87913e06-fcda-42a9-9423-b4228d04cd71")
    @autotest.name("SessionMonitor._escalated_in_spell: начальное значение False")
    def test_87913e06_escalated_in_spell_initialized_false(self):
        with autotest.step("Arrange: монитор по умолчанию"):
            m = _make_monitor()
        with autotest.step("Assert: _escalated_in_spell == False"):
            assert_false(
                m._escalated_in_spell, "_escalated_in_spell должен быть False при инициализации"
            )
