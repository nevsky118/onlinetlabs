from datetime import UTC, datetime, timedelta

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_greater,
    assert_greater_equal,
    assert_less_equal,
    assert_true,
)

from agents.analytics.models import StudentMetrics
from agents.analytics.tools import AnalyticsTools
from tests.settings.data.analytics_data import AttemptData

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestAnalyticsTools:
    @autotest.num("430")
    @autotest.external_id("6d074df2-864f-4449-aba9-cdff6d56cb82")
    @autotest.name("AnalyticsTools.compute_metrics: вычисляет метрики")
    def test_6d074df2_compute_metrics(self):
        now = datetime.now(tz=UTC)
        with autotest.step("Создаём 3 попытки: 2 pass, 1 fail"):
            attempts = [
                AttemptData(
                    step_slug="step-1",
                    result="pass",
                    attempt_number=1,
                    started_at=now - timedelta(minutes=10),
                    ended_at=now - timedelta(minutes=5),
                ),
                AttemptData(
                    id="a2",
                    step_slug="step-1",
                    result="fail",
                    attempt_number=2,
                    started_at=now - timedelta(minutes=4),
                    ended_at=now - timedelta(minutes=2),
                ),
                AttemptData(
                    id="a3",
                    step_slug="step-2",
                    result="pass",
                    attempt_number=1,
                    started_at=now - timedelta(minutes=2),
                    ended_at=now,
                ),
            ]

        with autotest.step("Вычисляем метрики"):
            tools = AnalyticsTools(db=None)
            metrics = tools.compute_metrics(attempts)

        with autotest.step("Проверяем StudentMetrics"):
            assert_true(isinstance(metrics, StudentMetrics), f"тип: {type(metrics)}")
            assert_equal(metrics.total_attempts, 3, "3 попытки")
            assert_greater_equal(metrics.success_rate, 0.6, "success_rate >= 0.6")
            assert_less_equal(metrics.success_rate, 0.7, "success_rate <= 0.7")
            assert_greater(metrics.avg_time_per_step, 0, "время > 0")

    @autotest.num("431")
    @autotest.external_id("f2a3b4c5-d6e7-4f89-9abc-def012340002")
    @autotest.name("AnalyticsTools.compute_metrics: пустой список")
    def test_f2a3b4c5_compute_metrics_empty(self):
        with autotest.step("Вычисляем метрики из пустого списка"):
            tools = AnalyticsTools(db=None)
            metrics = tools.compute_metrics([])

        with autotest.step("Проверяем нулевые метрики"):
            assert_equal(metrics.total_attempts, 0, "0 попыток")
            assert_equal(metrics.success_rate, 0.0, "0% успеха")
            assert_equal(metrics.avg_time_per_step, 0.0, "0 времени")
            assert_equal(metrics.struggling_steps, [], "нет проблемных шагов")

    @autotest.num("432")
    @autotest.external_id("d0d3c8c7-2659-48a3-858b-c5868080cdee")
    @autotest.name("AnalyticsTools.compute_metrics: определяет struggling шаги")
    def test_d0d3c8c7_compute_metrics_struggling(self):
        now = datetime.now(tz=UTC)
        with autotest.step("Создаём 3 неудачи подряд на step-1"):
            attempts = [
                AttemptData(
                    id=f"a{i}",
                    step_slug="step-1",
                    result="fail",
                    attempt_number=i,
                    started_at=now - timedelta(minutes=10 - i),
                    ended_at=now - timedelta(minutes=9 - i),
                )
                for i in range(1, 4)
            ]

        with autotest.step("Вычисляем метрики"):
            tools = AnalyticsTools(db=None)
            metrics = tools.compute_metrics(attempts)

        with autotest.step("Проверяем struggling_steps"):
            assert_true("step-1" in metrics.struggling_steps, "step-1 должен быть проблемным")

    @autotest.num("433")
    @autotest.external_id("d6e64c33-fa82-4571-a71a-cd49b3bc1d22")
    @autotest.name("AnalyticsTools.detect_error_patterns: повторяющиеся ошибки")
    def test_d6e64c33_detect_error_patterns(self):
        with autotest.step("Создаём попытки с повторяющимися ошибками"):
            attempts = [
                AttemptData(id="a1", result="fail", error_details="timeout on ping"),
                AttemptData(id="a2", result="fail", error_details="timeout on ping"),
                AttemptData(id="a3", result="fail", error_details="wrong interface"),
            ]

        with autotest.step("Ищем паттерны"):
            tools = AnalyticsTools(db=None)
            patterns = tools.detect_error_patterns(attempts)

        with autotest.step("Проверяем результат"):
            assert_true("timeout on ping" in patterns, "timeout on ping должен быть в паттернах")

    @autotest.num("434")
    @autotest.external_id("6b9b93c2-2235-4683-8bdc-293ee2b723aa")
    @autotest.name("AnalyticsTools.detect_error_patterns: нет повторов")
    def test_6b9b93c2_detect_error_patterns_no_repeats(self):
        with autotest.step("Создаём попытки с уникальными ошибками"):
            attempts = [
                AttemptData(id="a1", result="fail", error_details="error A"),
                AttemptData(id="a2", result="fail", error_details="error B"),
            ]

        with autotest.step("Ищем паттерны"):
            tools = AnalyticsTools(db=None)
            patterns = tools.detect_error_patterns(attempts)

        with autotest.step("Проверяем пустой результат"):
            assert_equal(patterns, [], "не должно быть паттернов")

    @autotest.num("435")
    @autotest.external_id("99de55ca-74e9-4f2f-80d0-921c49dbf5bf")
    @autotest.name("AnalyticsTools.detect_error_patterns: все успешные")
    def test_99de55ca_detect_error_patterns_all_pass(self):
        with autotest.step("Создаём только успешные попытки"):
            attempts = [
                AttemptData(id="a1", result="pass"),
                AttemptData(id="a2", result="pass"),
            ]

        with autotest.step("Ищем паттерны"):
            tools = AnalyticsTools(db=None)
            patterns = tools.detect_error_patterns(attempts)

        with autotest.step("Проверяем пустой результат"):
            assert_equal(patterns, [], "нет ошибок")
