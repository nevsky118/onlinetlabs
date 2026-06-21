import pytest
from unittest.mock import MagicMock
from config.config_model import LearningAnalyticsConfig
from learning_analytics.monitor import SessionMonitor
pytestmark = [pytest.mark.unit]

def _monitor(thresholds):
    cfg = LearningAnalyticsConfig()
    cfg.dwell_thresholds = thresholds
    m = SessionMonitor(mcp_client=MagicMock(), db_factory=MagicMock(),
        orchestrator=MagicMock(), learning_analytics_config=cfg)
    return m

def test_dwell_gate():
    m = _monitor({"idle": 30.0, "stuck_on_step": 0.0, "repeating_errors": 0.0, "trial_and_error": 0.0})
    assert m._dwell_ready("idle", 15.0) is False     # ниже T_k
    assert m._dwell_ready("idle", 30.0) is True      # достигнут T_k
    assert m._dwell_ready("productive", 999.0) is False  # хороший режим — не триггерим
    assert m._dwell_ready("stuck_on_step", 0.0) is True  # T_k=0 baseline → сразу
