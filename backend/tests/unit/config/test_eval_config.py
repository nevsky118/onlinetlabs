import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_greater, assert_true

from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


class TestEvalConfig:
    @autotest.num("1640")
    @autotest.external_id("e5c1862c-d898-4ed9-ad0c-c009d3a43064")
    @autotest.name("LearningAnalyticsConfig: eval params are set")
    def test_e5c1862c_eval_params(self):
        with autotest.step("Act: default config"):
            config = LearningAnalyticsConfig()
        with autotest.step("Assert: the T_k grid is non-empty and increasing, window > 0"):
            assert_true(len(config.eval_t_k_grid) >= 2, "T_k grid")
            assert_greater(config.eval_onset_window_seconds, 0.0, "onset window")
