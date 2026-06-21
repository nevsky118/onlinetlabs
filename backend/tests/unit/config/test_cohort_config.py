import pytest
from config.config_model import LearningAnalyticsConfig
pytestmark = [pytest.mark.unit]

def test_cohort_params_defaults():
    c = LearningAnalyticsConfig()
    assert c.cohort_horizon_days > 0
    assert c.autonomy_intervention_threshold >= 0
