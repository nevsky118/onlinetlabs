"""Operating curve test over T_k + J-optimum (Task 7)."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from analytics.criterion import Costs
from analytics.metrics.metrics import j_optimal, operating_curve
from analytics.metrics.scenarios import make_normal_scenario, make_struggle_scenario
from analytics.runtime.process_state import ProcessRegime
from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


class TestCurve:
    @autotest.num("2600")
    @autotest.external_id("9a885646-af51-4343-873a-8aa4a7caaa58")
    @autotest.name("curve: false/hour does not increase with T_k; J-optimum selected")
    def test_9a885646_curve_monotone(self):
        with autotest.step("Arrange: mix of struggle+normal"):
            scns = [
                make_struggle_scenario(ProcessRegime.REPEATING_ERRORS, onset_index=3)
                for _ in range(3)
            ] + [make_normal_scenario(n=12) for _ in range(3)]
            cfg = LearningAnalyticsConfig()
            costs = Costs(c_stuck=1.0, c_intervention=1.0, c_false=5.0)
        with autotest.step("Act"):
            curve = operating_curve(scns, [0.0, 30.0, 120.0], cfg, costs)
            best = j_optimal(curve)
        with autotest.step(
            "Assert: curve matches the grid; false/hour non-increasing; J-optimum in the set"
        ):
            assert_equal(len(curve), 3, "points match the grid")
            fph = [point.false_per_hour for point in curve]
            assert_true(
                all(fph[i] >= fph[i + 1] for i in range(len(fph) - 1)),
                "false/hour does not increase with T_k",
            )
            assert_true(best in curve, "J-optimum is a point on the curve")

    @autotest.num("2601")
    @autotest.external_id("b3e7f2a1-04dc-4e8f-93b0-6d1c5e9f3a72")
    @autotest.name(
        "curve: J is non-degenerate, early intervention beats late under expensive stuck"
    )
    def test_b3e7f2a1_j_non_degenerate(self):
        with autotest.step("Arrange: long spells + high c_stuck"):
            scns = [
                make_struggle_scenario(
                    ProcessRegime.REPEATING_ERRORS, onset_index=2, n=12, step=15.0
                )
                for _ in range(4)
            ] + [make_normal_scenario(n=12) for _ in range(2)]
            cfg = LearningAnalyticsConfig()
            costs = Costs(c_stuck=2.0, c_intervention=1.0, c_false=2.0)
        with autotest.step("Act"):
            curve = operating_curve(scns, [0.0, 15.0, 300.0], cfg, costs)
        with autotest.step("Assert: J(t_k=0) < J(t_k=300), truncation removes degeneracy"):
            assert_equal(len(curve), 3, "three points match the grid")
            assert_true(
                curve[0].J < curve[-1].J,
                f"J(t_k=0)={curve[0].J:.3f} must be < J(t_k=300)={curve[-1].J:.3f}",
            )
