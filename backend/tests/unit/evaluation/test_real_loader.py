import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from evaluation.real_loader import cohens_kappa, labeled_real_count
from evaluation.scenarios import make_normal_scenario, make_struggle_scenario
from learning_analytics.process_state import ProcessRegime

pytestmark = [pytest.mark.unit]


class TestRealLoader:
    @autotest.num("1710")
    @autotest.external_id("b116df3a-1b9f-4873-94e8-0e4906ff379d")
    @autotest.name("real_loader: Cohen's κ = 1 при полном согласии, < 1 при расхождении")
    def test_b116df3a_kappa(self):
        with autotest.step("Act+Assert: полное согласие → κ=1"):
            assert_equal(cohens_kappa(["a", "b", "a"], ["a", "b", "a"]), 1.0, "κ полного согласия")
        with autotest.step("Assert: расхождение → κ<1"):
            assert_true(cohens_kappa(["a", "b", "a"], ["a", "a", "b"]) < 1.0, "κ при расхождении")

    @autotest.num("1711")
    @autotest.external_id("d14987a3-1a41-4331-a279-c7e592c38211")
    @autotest.name("real_loader: labeled-real-N считает реальные С метками, не harvested")
    def test_d14987a3_labeled_real(self):
        with autotest.step("Arrange: 1 real-струггл, 1 real-нормальная, 1 synthetic"):
            r1 = make_struggle_scenario(ProcessRegime.IDLE, source="real")
            r2 = make_normal_scenario(source="real")
            syn = make_struggle_scenario(ProcessRegime.IDLE, source="synthetic")
        with autotest.step("Act+Assert: labeled-real = 2, synthetic не в счёт"):
            assert_equal(labeled_real_count([r1, r2, syn]), 2, "labeled real")
