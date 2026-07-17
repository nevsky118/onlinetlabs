"""Tests for compute_arm_analysis: open vs closed arm on A4-5 metrics."""

from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_greater, assert_true

from experiment.analysis import compute_arm_analysis

pytestmark = [pytest.mark.unit]


def _m(arm: str, esc: int, l2_pass: bool | None, repeated: int) -> SimpleNamespace:
    return SimpleNamespace(
        base_arm=arm,  # training-arm; analysis.py groups by base_arm
        control_arm=arm,  # effective arm (audit); matches base_arm here
        escalations=esc,
        l2_unassisted_pass=l2_pass,
        repeated_errors=repeated,
    )


def _make_dataset() -> list:
    # open: many escalations, L2 fails more often, more repeated_errors
    open_metrics = [_m("open", esc=5, l2_pass=False, repeated=8) for _ in range(10)]
    open_metrics += [_m("open", esc=4, l2_pass=True, repeated=6) for _ in range(5)]
    # closed: fewer escalations, L2 passes more often, fewer repeated_errors
    closed_metrics = [_m("closed", esc=1, l2_pass=True, repeated=2) for _ in range(10)]
    closed_metrics += [_m("closed", esc=2, l2_pass=False, repeated=3) for _ in range(5)]
    return open_metrics + closed_metrics


class TestArmAnalysis:
    @autotest.num("1092")
    @autotest.external_id("fb22080e-7c17-4b6d-abf6-165896b9c075")
    @autotest.name("compute_arm_analysis: mentor_hours_saved > 0 когда open эскалирует больше")
    def test_fb22080e_mentor_hours_saved_positive(self):
        with autotest.step("Создаём датасет"):
            metrics = _make_dataset()

        with autotest.step("Запускаем анализ"):
            result = compute_arm_analysis(metrics, mentor_seconds=900.0)

        with autotest.step("mentor_hours_saved > 0"):
            assert_greater(result.mentor_hours_saved, 0, "closed сохраняет часы ментора")

    @autotest.num("1093")
    @autotest.external_id("3a04493e-33c6-48e3-89ff-803d66905cca")
    @autotest.name("compute_arm_analysis: l2_pass_rate_closed >= l2_pass_rate_open")
    def test_3a04493e_l2_pass_rate_closed_higher(self):
        with autotest.step("Создаём датасет"):
            metrics = _make_dataset()

        with autotest.step("Запускаем анализ"):
            result = compute_arm_analysis(metrics)

        with autotest.step("closed L2 pass rate выше"):
            assert_true(
                result.l2_pass_rate_closed >= result.l2_pass_rate_open,
                "closed arm проходит L2 лучше",
            )

    @autotest.num("1094")
    @autotest.external_id("3367a7c1-07fc-4369-a4b2-a389ba4d03ab")
    @autotest.name("compute_arm_analysis: escalations_mean_open > escalations_mean_closed")
    def test_3367a7c1_escalations_open_higher(self):
        with autotest.step("Создаём датасет"):
            metrics = _make_dataset()

        with autotest.step("Запускаем анализ"):
            result = compute_arm_analysis(metrics)

        with autotest.step("open эскалирует больше"):
            assert_greater(
                result.escalations_mean_open,
                result.escalations_mean_closed,
                "open arm mean escalations выше",
            )

    @autotest.num("1095")
    @autotest.external_id("2de2ecef-c4df-4cf8-8b87-5bd82670c47d")
    @autotest.name("compute_arm_analysis: repeated_errors comparison содержит t-тест")
    def test_2de2ecef_repeated_errors_comparison(self):
        with autotest.step("Создаём датасет"):
            metrics = _make_dataset()

        with autotest.step("Запускаем анализ"):
            result = compute_arm_analysis(metrics)

        with autotest.step("repeated_errors_comparison содержит ключи Welch t-test"):
            cmp = result.repeated_errors_comparison
            assert_true("t_statistic" in cmp, "есть t_statistic")
            assert_true("p_value" in cmp, "есть p_value")
            assert_true("cohens_d" in cmp, "есть cohens_d")

    @autotest.num("1096")
    @autotest.external_id("aec72172-d3f2-43da-b805-7a6218aab6e1")
    @autotest.name("compute_arm_analysis: пустой вход не падает")
    def test_aec72172_empty_input_no_crash(self):
        with autotest.step("Пустой список"):
            result = compute_arm_analysis([])

        with autotest.step("Все rate = 0.0, hours = 0.0"):
            assert_equal(result.l2_pass_rate_open, 0.0, "open L2 rate = 0")
            assert_equal(result.l2_pass_rate_closed, 0.0, "closed L2 rate = 0")
            assert_equal(result.escalations_mean_open, 0.0, "open esc mean = 0")
            assert_equal(result.escalations_mean_closed, 0.0, "closed esc mean = 0")
            assert_equal(result.mentor_hours_saved, 0.0, "0 часов сохранено")

    @autotest.num("1097")
    @autotest.external_id("b17ee300-bedc-4843-9208-4065d2596dd4")
    @autotest.name("compute_arm_analysis: только один arm не падает")
    def test_b17ee300_single_arm_no_crash(self):
        with autotest.step("Только open arm"):
            metrics = [_m("open", esc=3, l2_pass=True, repeated=4) for _ in range(5)]
            result = compute_arm_analysis(metrics)

        with autotest.step("closed = 0.0, insufficient_data в repeated_errors"):
            assert_equal(result.l2_pass_rate_closed, 0.0, "closed L2 rate = 0")
            assert_equal(result.escalations_mean_closed, 0.0, "closed esc mean = 0")
            assert_true(
                "error" in result.repeated_errors_comparison,
                "insufficient data при одном arm",
            )
