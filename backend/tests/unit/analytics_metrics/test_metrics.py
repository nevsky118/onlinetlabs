import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true

from analytics.metrics.harness import Detection
from analytics.metrics.metrics import bootstrap_ci, evaluate
from analytics.metrics.scenarios import make_normal_scenario, make_struggle_scenario
from analytics.runtime.process_state import ProcessRegime

pytestmark = [pytest.mark.unit]


class TestMetrics:
    @autotest.num("1670")
    @autotest.external_id("e44cc247-9f18-407c-b2fd-7ba446e6ae37")
    @autotest.name("metrics: TP/recall/latency/false-per-hour from detections")
    def test_e44cc247_evaluate(self):
        with autotest.step(
            "Arrange: 1 struggle detected in window, 1 missed, 1 normal false positive"
        ):
            s_hit = make_struggle_scenario(
                ProcessRegime.REPEATING_ERRORS, onset_index=4, n=12, step=15.0
            )  # onset 60
            s_miss = make_struggle_scenario(ProcessRegime.IDLE, onset_index=4, n=12, step=15.0)
            s_norm = make_normal_scenario(n=12, step=15.0)  # duration 180s
            pairs = [
                (
                    s_hit,
                    Detection(True, 75.0, ProcessRegime.REPEATING_ERRORS),
                ),  # within window [60,90]
                (s_miss, Detection(False, None, None)),  # miss
                (s_norm, Detection(True, 30.0, ProcessRegime.STUCK_ON_STEP)),  # false positive
            ]
        with autotest.step("Act"):
            matrix = evaluate(pairs)
        with autotest.step("Assert: recall 0.5, 1 false positive, latency=15"):
            assert_equal(matrix.n_struggle, 2, "struggle scenarios")
            assert_equal(matrix.n_tp, 1, "TP")
            assert_equal(matrix.recall, 0.5, "recall")
            assert_equal(matrix.latency_median, 15.0, "latency 75-60")
            assert_true(matrix.false_per_hour > 0.0, "false/hour>0")

    @autotest.num("1671")
    @autotest.external_id("14b97f36-3d40-474a-ab1b-eab2fa49aa84")
    @autotest.name("metrics: bootstrap CI is None for a single value")
    def test_14b97f36_ci_small(self):
        with autotest.step("Act+Assert"):
            assert_is_none(bootstrap_ci([5.0]), "single value, no CI")
            lo, hi = bootstrap_ci([10.0, 12.0, 14.0, 16.0, 18.0])
            assert_true(lo <= hi, "CI ordered")
