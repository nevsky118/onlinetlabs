import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_greater_equal, assert_true

from analytics.metrics.metrics import first_match_diagnostics
from analytics.metrics.scenarios import make_normal_scenario, make_struggle_scenario
from analytics.runtime.process_state import ProcessRegime
from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


class TestFirstMatch:
    @autotest.num("1690")
    @autotest.external_id("f8a7fbd6-d1fb-4c48-963b-20e3a53301bd")
    @autotest.name("first_match: diagnostics for multi-matches and order-sensitivity")
    def test_f8a7fbd6_diagnostics(self):
        with autotest.step("Arrange: trial_and_error trips >1 rule (distinct + entropy/freq)"):
            scenario = make_struggle_scenario(ProcessRegime.TRIAL_AND_ERROR, onset_index=4, n=12)
        with autotest.step("Act"):
            diag = first_match_diagnostics([scenario], LearningAnalyticsConfig())
        with autotest.step("Assert: there are firings, rates in [0,1], key structure correct"):
            assert_greater_equal(diag["total_firing_snapshots"], 1, "there are firings")
            assert_true(0.0 <= diag["multi_match_rate"] <= 1.0, "multi-match rate in [0,1]")
            assert_true(0.0 <= diag["order_sensitive_rate"] <= 1.0, "order-sensitive rate in [0,1]")

    @autotest.num("1691")
    @autotest.external_id("afa65da7-bcbb-4413-8a33-50c182a057dc")
    @autotest.name("first_match: normal scenario, no firings")
    def test_afa65da7_no_firing_normal(self):
        with autotest.step("Arrange: normal session (benign features)"):
            scenario = make_normal_scenario(n=8)
        with autotest.step("Act"):
            diag = first_match_diagnostics([scenario], LearningAnalyticsConfig())
        with autotest.step("Assert: no firings, rates 0"):
            assert_equal(diag["total_firing_snapshots"], 0, "no firings")
            assert_equal(diag["multi_match_rate"], 0.0, "multi_match_rate=0")
            assert_equal(diag["order_sensitive_rate"], 0.0, "order_sensitive_rate=0")
