import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true

from evaluation.harness import Detection
from evaluation.metrics import bootstrap_ci, evaluate
from evaluation.scenarios import make_normal_scenario, make_struggle_scenario
from learning_analytics.process_state import ProcessRegime

pytestmark = [pytest.mark.unit]


class TestMetrics:
    @autotest.num("1670")
    @autotest.external_id("e44cc247-9f18-407c-b2fd-7ba446e6ae37")
    @autotest.name("metrics: TP/recall/latency/ложные-час по детекциям")
    def test_e44cc247_evaluate(self):
        with autotest.step("Arrange: 1 струггл детектнут в окне, 1 пропущен, 1 нормальная ложная"):
            s_hit = make_struggle_scenario(
                ProcessRegime.REPEATING_ERRORS, onset_index=4, n=12, step=15.0
            )  # онсет 60
            s_miss = make_struggle_scenario(ProcessRegime.IDLE, onset_index=4, n=12, step=15.0)
            s_norm = make_normal_scenario(n=12, step=15.0)  # длительность 180с
            pairs = [
                (s_hit, Detection(True, 75.0, ProcessRegime.REPEATING_ERRORS)),  # в окне [60,90]
                (s_miss, Detection(False, None, None)),  # пропуск
                (s_norm, Detection(True, 30.0, ProcessRegime.STUCK_ON_STEP)),  # ложное
            ]
        with autotest.step("Act"):
            m = evaluate(pairs)
        with autotest.step("Assert: recall 0.5, 1 ложное, latency=15"):
            assert_equal(m.n_struggle, 2, "струггл-сценариев")
            assert_equal(m.n_tp, 1, "TP")
            assert_equal(m.recall, 0.5, "recall")
            assert_equal(m.latency_median, 15.0, "latency 75-60")
            assert_true(m.false_per_hour > 0.0, "ложные/час>0")

    @autotest.num("1671")
    @autotest.external_id("14b97f36-3d40-474a-ab1b-eab2fa49aa84")
    @autotest.name("metrics: бутстрэп-CI None на одном значении")
    def test_14b97f36_ci_small(self):
        with autotest.step("Act+Assert"):
            assert_is_none(bootstrap_ci([5.0]), "одно значение — нет CI")
            lo, hi = bootstrap_ci([10.0, 12.0, 14.0, 16.0, 18.0])
            assert_true(lo <= hi, "CI упорядочен")
