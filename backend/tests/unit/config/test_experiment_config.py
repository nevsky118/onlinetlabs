import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_greater, assert_greater_equal

from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


class TestExperimentConfig:
    @autotest.num("1272")
    @autotest.external_id("ba8bba52-af24-410d-9cbc-899f3e465de6")
    @autotest.name(
        "LearningAnalyticsConfig: ключевые параметры эксперимента имеют допустимые значения"
    )
    def test_ba8bba52_experiment_params(self):
        with autotest.step("Act: создаём конфиг по умолчанию"):
            c = LearningAnalyticsConfig()
        with autotest.step("Assert: параметры в допустимых диапазонах"):
            assert_greater(c.escalation_max_dwell, 0, "escalation_max_dwell > 0")
            assert_greater(c.mentor_handling_seconds, 0, "mentor_handling_seconds > 0")
            assert_greater_equal(c.l2_intervention_cap, 0, "l2_intervention_cap >= 0")
