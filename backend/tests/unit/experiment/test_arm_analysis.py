"""Тесты compute_arm_analysis: open vs closed arm по A4-5 метрикам."""

from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_greater, assert_true

from experiment.analysis import compute_arm_analysis

pytestmark = [pytest.mark.unit]


def _m(arm: str, esc: int, l2_pass: bool | None, repeated: int) -> SimpleNamespace:
    return SimpleNamespace(
        base_arm=arm,       # training-arm; analysis.py группирует по base_arm
        control_arm=arm,    # effective arm (аудит); здесь совпадает с base_arm
        escalations=esc,
        l2_unassisted_pass=l2_pass,
        repeated_errors=repeated,
    )


def _make_dataset() -> list:
    # open: много эскалаций, L2 падает чаще, больше repeated_errors
    open_metrics = [_m("open", esc=5, l2_pass=False, repeated=8) for _ in range(10)]
    open_metrics += [_m("open", esc=4, l2_pass=True, repeated=6) for _ in range(5)]
    # closed: меньше эскалаций, L2 проходит чаще, меньше repeated_errors
    closed_metrics = [_m("closed", esc=1, l2_pass=True, repeated=2) for _ in range(10)]
    closed_metrics += [_m("closed", esc=2, l2_pass=False, repeated=3) for _ in range(5)]
    return open_metrics + closed_metrics


class TestArmAnalysis:
    @autotest.num("630")
    @autotest.external_id("a1b2c3d4-e5f6-4789-abcd-630000000001")
    @autotest.name("compute_arm_analysis: mentor_hours_saved > 0 когда open эскалирует больше")
    def test_a1b2c3d4_mentor_hours_saved_positive(self):
        with autotest.step("Создаём датасет"):
            metrics = _make_dataset()

        with autotest.step("Запускаем анализ"):
            result = compute_arm_analysis(metrics, mentor_seconds=900.0)

        with autotest.step("mentor_hours_saved > 0"):
            assert_greater(result.mentor_hours_saved, 0, "closed сохраняет часы ментора")

    @autotest.num("631")
    @autotest.external_id("b2c3d4e5-f6a7-4890-bcde-631000000002")
    @autotest.name("compute_arm_analysis: l2_pass_rate_closed >= l2_pass_rate_open")
    def test_b2c3d4e5_l2_pass_rate_closed_higher(self):
        with autotest.step("Создаём датасет"):
            metrics = _make_dataset()

        with autotest.step("Запускаем анализ"):
            result = compute_arm_analysis(metrics)

        with autotest.step("closed L2 pass rate выше"):
            assert_true(
                result.l2_pass_rate_closed >= result.l2_pass_rate_open,
                "closed arm проходит L2 лучше",
            )

    @autotest.num("632")
    @autotest.external_id("c3d4e5f6-a7b8-4901-cdef-632000000003")
    @autotest.name("compute_arm_analysis: escalations_mean_open > escalations_mean_closed")
    def test_c3d4e5f6_escalations_open_higher(self):
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

    @autotest.num("633")
    @autotest.external_id("d4e5f6a7-b8c9-4012-defa-633000000004")
    @autotest.name("compute_arm_analysis: repeated_errors comparison содержит t-тест")
    def test_d4e5f6a7_repeated_errors_comparison(self):
        with autotest.step("Создаём датасет"):
            metrics = _make_dataset()

        with autotest.step("Запускаем анализ"):
            result = compute_arm_analysis(metrics)

        with autotest.step("repeated_errors_comparison содержит ключи Welch t-test"):
            cmp = result.repeated_errors_comparison
            assert_true("t_statistic" in cmp, "есть t_statistic")
            assert_true("p_value" in cmp, "есть p_value")
            assert_true("cohens_d" in cmp, "есть cohens_d")

    @autotest.num("634")
    @autotest.external_id("e5f6a7b8-c9d0-4123-efab-634000000005")
    @autotest.name("compute_arm_analysis: пустой вход не падает")
    def test_e5f6a7b8_empty_input_no_crash(self):
        with autotest.step("Пустой список"):
            result = compute_arm_analysis([])

        with autotest.step("Все rate = 0.0, hours = 0.0"):
            assert_equal(result.l2_pass_rate_open, 0.0, "open L2 rate = 0")
            assert_equal(result.l2_pass_rate_closed, 0.0, "closed L2 rate = 0")
            assert_equal(result.escalations_mean_open, 0.0, "open esc mean = 0")
            assert_equal(result.escalations_mean_closed, 0.0, "closed esc mean = 0")
            assert_equal(result.mentor_hours_saved, 0.0, "0 часов сохранено")

    @autotest.num("635")
    @autotest.external_id("f6a7b8c9-d0e1-4234-fabc-635000000006")
    @autotest.name("compute_arm_analysis: только один arm не падает")
    def test_f6a7b8c9_single_arm_no_crash(self):
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
