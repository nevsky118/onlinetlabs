import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


class TestSimConfig:
    @autotest.num("2012")
    @autotest.external_id("7b08b35d-9161-44b3-9788-9b376f17121b")
    @autotest.name("Config: sim_llm_help_enabled по умолчанию False")
    def test_7b08b35d_sim_llm_help_default(self):
        with autotest.step("Act+Assert: дефолт выключен"):
            assert_equal(LearningAnalyticsConfig().sim_llm_help_enabled, False, "по умолчанию False")
