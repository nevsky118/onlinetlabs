import pytest
from datetime import datetime, timedelta, timezone

from agents.analytics.models import DifficultyRecommendation, StudentMetrics
from agents.analytics.tools import AnalyticsTools
from agents.analytics.agent import AnalyticsAgent
from tests.unit.agents.conftest import make_attempt
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_true,
    assert_greater,
    assert_greater_equal,
    assert_less_equal,
)

pytestmark = [pytest.mark.unit, pytest.mark.agents]


# ---------------------------------------------------------------------------
# AnalyticsTools
# ---------------------------------------------------------------------------

class TestAnalyticsTools:
    @autotest.num("430")
    @autotest.external_id("agents-analytics-tools-compute-metrics-success")
    @autotest.name("AnalyticsTools.compute_metrics: вычисляет метрики")
    def test_compute_metrics(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём 3 попытки: 2 pass, 1 fail"):
            attempts = [
                make_attempt(
                    step_slug="step-1", result="pass", attempt_number=1,
                    started_at=now - timedelta(minutes=10),
                    ended_at=now - timedelta(minutes=5),
                ),
                make_attempt(
                    id="a2", step_slug="step-1", result="fail", attempt_number=2,
                    started_at=now - timedelta(minutes=4),
                    ended_at=now - timedelta(minutes=2),
                ),
                make_attempt(
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
    @autotest.external_id("agents-analytics-tools-compute-metrics-empty")
    @autotest.name("AnalyticsTools.compute_metrics: пустой список")
    def test_compute_metrics_empty(self):
        with autotest.step("Вычисляем метрики из пустого списка"):
            tools = AnalyticsTools(db=None)
            metrics = tools.compute_metrics([])

        with autotest.step("Проверяем нулевые метрики"):
            assert_equal(metrics.total_attempts, 0, "0 попыток")
            assert_equal(metrics.success_rate, 0.0, "0% успеха")
            assert_equal(metrics.avg_time_per_step, 0.0, "0 времени")
            assert_equal(metrics.struggling_steps, [], "нет проблемных шагов")

    @autotest.num("432")
    @autotest.external_id("agents-analytics-tools-compute-metrics-struggling")
    @autotest.name("AnalyticsTools.compute_metrics: определяет struggling шаги")
    def test_compute_metrics_struggling(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём 3 неудачи подряд на step-1"):
            attempts = [
                make_attempt(
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
    @autotest.external_id("agents-analytics-tools-detect-error-patterns")
    @autotest.name("AnalyticsTools.detect_error_patterns: повторяющиеся ошибки")
    def test_detect_error_patterns(self):
        with autotest.step("Создаём попытки с повторяющимися ошибками"):
            attempts = [
                make_attempt(id="a1", result="fail", error_details="timeout on ping"),
                make_attempt(id="a2", result="fail", error_details="timeout on ping"),
                make_attempt(id="a3", result="fail", error_details="wrong interface"),
            ]

        with autotest.step("Ищем паттерны"):
            tools = AnalyticsTools(db=None)
            patterns = tools.detect_error_patterns(attempts)

        with autotest.step("Проверяем результат"):
            assert_true("timeout on ping" in patterns, "timeout on ping должен быть в паттернах")

    @autotest.num("434")
    @autotest.external_id("agents-analytics-tools-detect-error-patterns-none")
    @autotest.name("AnalyticsTools.detect_error_patterns: нет повторов")
    def test_detect_error_patterns_no_repeats(self):
        with autotest.step("Создаём попытки с уникальными ошибками"):
            attempts = [
                make_attempt(id="a1", result="fail", error_details="error A"),
                make_attempt(id="a2", result="fail", error_details="error B"),
            ]

        with autotest.step("Ищем паттерны"):
            tools = AnalyticsTools(db=None)
            patterns = tools.detect_error_patterns(attempts)

        with autotest.step("Проверяем пустой результат"):
            assert_equal(patterns, [], "не должно быть паттернов")

    @autotest.num("435")
    @autotest.external_id("agents-analytics-tools-detect-no-errors")
    @autotest.name("AnalyticsTools.detect_error_patterns: все успешные")
    def test_detect_error_patterns_all_pass(self):
        with autotest.step("Создаём только успешные попытки"):
            attempts = [
                make_attempt(id="a1", result="pass"),
                make_attempt(id="a2", result="pass"),
            ]

        with autotest.step("Ищем паттерны"):
            tools = AnalyticsTools(db=None)
            patterns = tools.detect_error_patterns(attempts)

        with autotest.step("Проверяем пустой результат"):
            assert_equal(patterns, [], "нет ошибок")


# ---------------------------------------------------------------------------
# AnalyticsAgent
# ---------------------------------------------------------------------------

class TestAnalyticsAgent:
    @autotest.num("436")
    @autotest.external_id("agents-analytics-agent-init")
    @autotest.name("AnalyticsAgent: инициализация")
    def test_init(self, config_model):
        with autotest.step("Создаём AnalyticsAgent"):
            agent = AnalyticsAgent(config_model, db=None)

        with autotest.step("Проверяем атрибуты"):
            assert_true(agent.tools is not None, "tools не None")

    @autotest.num("437")
    @autotest.external_id("agents-analytics-agent-system-prompt")
    @autotest.name("AnalyticsAgent: system_prompt содержит роль")
    def test_system_prompt(self, config_model):
        with autotest.step("Получаем system_prompt"):
            agent = AnalyticsAgent(config_model, db=None)
            prompt = agent.system_prompt()

        with autotest.step("Проверяем содержание"):
            assert_true(len(prompt) > 10, "prompt содержательный")

    @autotest.num("438")
    @autotest.external_id("agents-analytics-agent-analyze-high-success")
    @autotest.name("AnalyticsAgent: analyze рекомендует advanced при высоком success_rate")
    def test_analyze_high_success(self, config_model):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём 10 успешных попыток"):
            attempts = [
                make_attempt(
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
    @autotest.external_id("agents-analytics-agent-analyze-low-success")
    @autotest.name("AnalyticsAgent: analyze рекомендует beginner при низком success_rate")
    def test_analyze_low_success(self, config_model):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём 10 неудачных попыток"):
            attempts = [
                make_attempt(
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
