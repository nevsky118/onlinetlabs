import pytest
from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


def test_experiment_params():
    c = LearningAnalyticsConfig()
    assert c.escalation_max_dwell > 0
    assert c.mentor_handling_seconds > 0
    assert c.l2_intervention_cap >= 0
