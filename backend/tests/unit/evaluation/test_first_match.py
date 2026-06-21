import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_true, assert_greater_equal, assert_equal
from config.config_model import LearningAnalyticsConfig
from learning_analytics.process_state import ProcessRegime
from evaluation.scenarios import make_struggle_scenario, make_normal_scenario
from evaluation.metrics import first_match_diagnostics

pytestmark = [pytest.mark.unit]


class TestFirstMatch:
    @autotest.num("1690")
    @autotest.external_id("f8a7fbd6-d1fb-4c48-963b-20e3a53301bd")
    @autotest.name("first_match: диагностика мульти-совпадений и order-sensitivity")
    def test_f8a7fbd6_diagnostics(self):
        with autotest.step("Arrange: trial_and_error пробивает >1 правила (distinct + entropy/freq)"):
            s = make_struggle_scenario(ProcessRegime.TRIAL_AND_ERROR, onset_index=4, n=12)
        with autotest.step("Act"):
            diag = first_match_diagnostics([s], LearningAnalyticsConfig())
        with autotest.step("Assert: есть сработавшие, доли в [0,1], структура ключей верна"):
            assert_greater_equal(diag["total_firing_snapshots"], 1, "есть срабатывания")
            assert_true(0.0 <= diag["multi_match_rate"] <= 1.0, "доля мульти в [0,1]")
            assert_true(0.0 <= diag["order_sensitive_rate"] <= 1.0, "доля order-sensitive в [0,1]")

    @autotest.num("1691")
    @autotest.external_id("afa65da7-bcbb-4413-8a33-50c182a057dc")
    @autotest.name("first_match: нормальный сценарий — нет срабатываний")
    def test_afa65da7_no_firing_normal(self):
        with autotest.step("Arrange: нормальная сессия (benign-фичи)"):
            s = make_normal_scenario(n=8)
        with autotest.step("Act"):
            diag = first_match_diagnostics([s], LearningAnalyticsConfig())
        with autotest.step("Assert: нет срабатываний, доли 0"):
            assert_equal(diag["total_firing_snapshots"], 0, "нет срабатываний")
            assert_equal(diag["multi_match_rate"], 0.0, "multi_match_rate=0")
            assert_equal(diag["order_sensitive_rate"], 0.0, "order_sensitive_rate=0")
