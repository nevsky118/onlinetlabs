import pytest
from datetime import datetime, timedelta, timezone

from agents.analytics.models import DifficultyRecommendation, StudentMetrics
from agents.analytics.tools import AnalyticsTools
from agents.analytics.agent import AnalyticsAgent
from tests.settings.data.analytics_data import AttemptData
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_true,
    assert_greater,
    assert_greater_equal,
    assert_less_equal,
)

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestAnalyticsTools:
    @autotest.num("430")
    @autotest.external_id("f1a2b3c4-d5e6-4f78-9abc-def012340001")
    @autotest.name("AnalyticsTools.compute_metrics: вычисляет метрики")
    def test_f1a2b3c4_compute_metrics(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём 3 попытки: 2 pass, 1 fail"):
            attempts = [
                AttemptData(
                    step_slug="step-1", result="pass", attempt_number=1,
                    started_at=now - timedelta(minutes=10),
                    ended_at=now - timedelta(minutes=5),
                ),
                AttemptData(
                    id="a2", step_slug="step-1", result="fail", attempt_number=2,
                    started_at=now - timedelta(minutes=4),
                    ended_at=now - timedelta(minutes=2),
                ),
                AttemptData(
                    id="a3", step_slug="step-2", result="pass", attempt_number=1,
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
    @autotest.external_id("f3a4b5c6-d7e8-4f90-9abc-def012340003")
    @autotest.name("AnalyticsTools.compute_metrics: определяет struggling шаги")
    def test_f3a4b5c6_compute_metrics_struggling(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём 3 неудачи подряд на step-1"):
            attempts = [
                AttemptData(
                    id=f"a{i}", step_slug="step-1", result="fail",
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
    @autotest.external_id("f4a5b6c7-d8e9-4fa1-9abc-def012340004")
    @autotest.name("AnalyticsTools.detect_error_patterns: повторяющиеся ошибки")
    def test_f4a5b6c7_detect_error_patterns(self):
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
    @autotest.external_id("f5a6b7c8-d9ea-4fb2-9abc-def012340005")
    @autotest.name("AnalyticsTools.detect_error_patterns: нет повторов")
    def test_f5a6b7c8_detect_error_patterns_no_repeats(self):
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
    @autotest.external_id("f6a7b8c9-daeb-4fc3-9abc-def012340006")
    @autotest.name("AnalyticsTools.detect_error_patterns: все успешные")
    def test_f6a7b8c9_detect_error_patterns_all_pass(self):
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


class TestAnalyticsAgent:
    @autotest.num("436")
    @autotest.external_id("f7a8b9ca-dbec-4fd4-9abc-def012340007")
    @autotest.name("AnalyticsAgent: инициализация")
    def test_f7a8b9ca_init(self, config_model):
        with autotest.step("Создаём AnalyticsAgent"):
            agent = AnalyticsAgent(config_model, db=None)

        with autotest.step("Проверяем атрибуты"):
            assert_true(agent.tools is not None, "tools не None")

    @autotest.num("437")
    @autotest.external_id("f8a9bacb-dced-4fe5-9abc-def012340008")
    @autotest.name("AnalyticsAgent: system_prompt содержит роль")
    def test_f8a9bacb_system_prompt(self, config_model):
        with autotest.step("Получаем system_prompt"):
            agent = AnalyticsAgent(config_model, db=None)
            prompt = agent.system_prompt()

        with autotest.step("Проверяем содержание"):
            assert_true(len(prompt) > 10, "prompt содержательный")

    @autotest.num("438")
    @autotest.external_id("f9aabbcc-ddee-4ff6-9abc-def012340009")
    @autotest.name("AnalyticsAgent: analyze рекомендует advanced при высоком success_rate")
    def test_f9aabbcc_analyze_high_success(self, config_model):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём 10 успешных попыток"):
            attempts = [
                AttemptData(
                    id=f"a{i}", step_slug=f"step-{i}", result="pass",
                    started_at=now - timedelta(minutes=i + 1),
                    ended_at=now - timedelta(minutes=i),
                )
                for i in range(10)
            ]
            agent = AnalyticsAgent(config_model, db=None)

        with autotest.step("Вызываем analyze"):
            result = agent.analyze(attempts, current_difficulty="intermediate")

        with autotest.step("Проверяем рекомендацию"):
            assert_true(isinstance(result, DifficultyRecommendation), f"тип: {type(result)}")
            assert_equal(result.recommended_difficulty, "advanced", "должен рекомендовать advanced")

    @autotest.num("439")
    @autotest.external_id("faaabbcd-deef-4f07-9abc-def012340010")
    @autotest.name("AnalyticsAgent: analyze рекомендует beginner при низком success_rate")
    def test_faaabbcd_analyze_low_success(self, config_model):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём 10 неудачных попыток"):
            attempts = [
                AttemptData(
                    id=f"a{i}", step_slug="step-1", result="fail",
                    started_at=now - timedelta(minutes=i + 1),
                    ended_at=now - timedelta(minutes=i),
                    error_details="failed",
                )
                for i in range(10)
            ]
            agent = AnalyticsAgent(config_model, db=None)

        with autotest.step("Вызываем analyze"):
            result = agent.analyze(attempts, current_difficulty="intermediate")

        with autotest.step("Проверяем рекомендацию"):
            assert_equal(result.recommended_difficulty, "beginner", "должен рекомендовать beginner")
