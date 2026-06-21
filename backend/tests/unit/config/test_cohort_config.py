import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_greater_equal, assert_greater

from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


class TestLearningAnalyticsConfig:
    @autotest.num("972")
    @autotest.external_id("a5dfe4a8-a32f-46f1-af42-c21552020d34")
    @autotest.name("LearningAnalyticsConfig: дефолтные значения когорты корректны")
    def test_a5dfe4a8_cohort_params_defaults(self):
        with autotest.step("Act: создать конфиг с дефолтами"):
            c = LearningAnalyticsConfig()

        with autotest.step("Assert: cohort_horizon_days > 0 и autonomy_intervention_threshold >= 0"):
            assert_greater(c.cohort_horizon_days, 0, "cohort_horizon_days > 0")
            assert_greater_equal(c.autonomy_intervention_threshold, 0, "autonomy_intervention_threshold >= 0")
