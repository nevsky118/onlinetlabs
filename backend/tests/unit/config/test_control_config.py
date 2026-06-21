import pytest
from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


def test_control_defaults():
    c = LearningAnalyticsConfig()
    assert isinstance(c.dwell_thresholds, dict)
    assert c.dwell_thresholds.get("stuck_on_step", 0.0) >= 0.0
    assert c.cost_stuck > 0 and c.cost_intervention > 0 and c.cost_false_intervention >= 0


def test_dwell_thresholds_has_all_regimes():
    c = LearningAnalyticsConfig()
    assert set(c.dwell_thresholds) == {"stuck_on_step", "repeating_errors", "idle", "trial_and_error"}
