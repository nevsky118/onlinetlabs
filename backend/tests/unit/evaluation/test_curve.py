"""Тест рабочей кривой по T_k + J-оптимум (Task 7)."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from config.config_model import LearningAnalyticsConfig
from control.criterion import Costs
from evaluation.metrics import j_optimal, operating_curve
from evaluation.scenarios import make_normal_scenario, make_struggle_scenario
from learning_analytics.process_state import ProcessRegime

pytestmark = [pytest.mark.unit]


class TestCurve:
    @autotest.num("1700")
    @autotest.external_id("9a885646-af51-4343-873a-8aa4a7caaa58")
    @autotest.name("curve: ложные/час не растут с T_k; J-оптимум выбран")
    def test_9a885646_curve_monotone(self):
        with autotest.step("Arrange: смесь струггл+нормальные"):
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
            "Assert: кривая по сетке; ложные/час невозрастающие; J-оптимум в наборе"
        ):
            assert_equal(len(curve), 3, "точки по сетке")
            fph = [p.false_per_hour for p in curve]
            assert_true(
                all(fph[i] >= fph[i + 1] for i in range(len(fph) - 1)),
                "ложные/час не растут с T_k",
            )
            assert_true(best in curve, "J-оптимум — точка кривой")

    @autotest.num("1701")
    @autotest.external_id("b3e7f2a1-04dc-4e8f-93b0-6d1c5e9f3a72")
    @autotest.name("curve: J не вырожден — раннее вмешательство лучше позднего при дорогом stuck")
    def test_b3e7f2a1_j_non_degenerate(self):
        with autotest.step("Arrange: длинные спеллы + высокий c_stuck"):
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
        with autotest.step("Assert: J(t_k=0) < J(t_k=300) — усечение устраняет вырождение"):
            assert_equal(len(curve), 3, "три точки по сетке")
            assert_true(
                curve[0].J < curve[-1].J,
                f"J(t_k=0)={curve[0].J:.3f} должен быть < J(t_k=300)={curve[-1].J:.3f}",
            )
