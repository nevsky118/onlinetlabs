import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_true, assert_greater
from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


class TestEvalConfig:
    @autotest.num("1640")
    @autotest.external_id("e5c1862c-d898-4ed9-ad0c-c009d3a43064")
    @autotest.name("LearningAnalyticsConfig: eval-параметры заданы")
    def test_e5c1862c_eval_params(self):
        with autotest.step("Act: дефолтный конфиг"):
            c = LearningAnalyticsConfig()
        with autotest.step("Assert: сетка T_k непуста и возрастает, окно > 0"):
            assert_true(len(c.eval_t_k_grid) >= 2, "сетка T_k")
            assert_greater(c.eval_onset_window_seconds, 0.0, "окно онсета")
