import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_instance, assert_true

from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


class TestControlConfig:
    @autotest.num("1392")
    @autotest.external_id("3d1bea8a-9cf6-4a9c-a7eb-85a397aa8bd6")
    @autotest.name("LearningAnalyticsConfig: default control values are correct")
    def test_3d1bea8a_control_defaults(self):
        with autotest.step("Act: create the default config"):
            config = LearningAnalyticsConfig()

        with autotest.step("Assert: dwell_thresholds is a dict, stuck_on_step >= 0, costs > 0"):
            assert_is_instance(config.dwell_thresholds, dict, "dwell_thresholds is dict")
            assert_true(
                config.dwell_thresholds.get("stuck_on_step", 0.0) >= 0.0, "stuck_on_step >= 0"
            )
            assert_true(config.cost_stuck > 0, "cost_stuck > 0")
            assert_true(config.cost_intervention > 0, "cost_intervention > 0")
            assert_true(config.cost_false_intervention >= 0, "cost_false_intervention >= 0")

    @autotest.num("1393")
    @autotest.external_id("9ecd9582-1ccc-4458-9785-49af12a9bf1e")
    @autotest.name("LearningAnalyticsConfig: dwell_thresholds contains all regimes")
    def test_9ecd9582_dwell_thresholds_has_all_regimes(self):
        with autotest.step("Act: create the default config"):
            config = LearningAnalyticsConfig()

        with autotest.step("Assert: dwell_thresholds keys match the expected set"):
            assert_equal(
                set(config.dwell_thresholds),
                {"stuck_on_step", "repeating_errors", "idle", "trial_and_error"},
                "all four regimes are present",
            )
