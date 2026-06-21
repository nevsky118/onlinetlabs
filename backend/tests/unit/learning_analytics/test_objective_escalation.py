import pytest
from unittest.mock import MagicMock

from config.config_model import LearningAnalyticsConfig
from learning_analytics.monitor import SessionMonitor

pytestmark = [pytest.mark.unit]


def _make_monitor(escalation_max_dwell=180.0):
    cfg = LearningAnalyticsConfig(escalation_max_dwell=escalation_max_dwell)
    return SessionMonitor(
        mcp_client=MagicMock(), db_factory=MagicMock(),
        orchestrator=MagicMock(), learning_analytics_config=cfg,
    )


def test_is_escalation_below_threshold():
    m = _make_monitor(escalation_max_dwell=180.0)
    assert m._is_escalation(120.0) is False


def test_is_escalation_at_threshold():
    m = _make_monitor(escalation_max_dwell=180.0)
    assert m._is_escalation(180.0) is True


def test_is_escalation_above_threshold():
    m = _make_monitor(escalation_max_dwell=180.0)
    assert m._is_escalation(300.0) is True


def test_escalated_in_spell_initialized_false():
    m = _make_monitor()
    assert m._escalated_in_spell is False
