import pytest
from agents.analytics.agent import AnalyticsAgent
from agents.analytics.models import (
    AnalyticsResult,
    SessionFeatures,
    StruggleType,
    SuggestedIntervention,
)
from config.config_model import LearningAnalyticsConfig
from tests.settings.data.analytics_data import SessionFeaturesData
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestAnalyticsAgentSession:
    @autotest.num("504")
    @autotest.external_id("e4f5a6b7-c8d9-4e0f-8a1b-2c3d4e5f6a7b")
    @autotest.name("AnalyticsAgent.analyze_session: нет проблем в нормальной сессии")
    def test_e4f5a6b7_no_struggle_normal_session(self, config_model):
        with autotest.step("Создаём агент и нормальные фичи"):
            agent = AnalyticsAgent(config_model, db=None)
            features = SessionFeatures(**SessionFeaturesData().data)

        with autotest.step("Вызываем analyze_session"):
            result = agent.analyze_session(features, LearningAnalyticsConfig())

        with autotest.step("Проверяем отсутствие struggle"):
            assert_true(isinstance(result, AnalyticsResult), f"тип: {type(result)}")
            assert_true(result.struggle_detected is False, "struggle не обнаружен")
            assert_equal(result.suggested_intervention, SuggestedIntervention.NONE, "нет интервенции")

    @autotest.num("505")
    @autotest.external_id("f5a6b7c8-d9e0-4f1a-9b2c-3d4e5f6a7b8c")
    @autotest.name("AnalyticsAgent.analyze_session: обнаруживает повторяющиеся ошибки")
    def test_f5a6b7c8_detects_repeating_errors(self, config_model):
        with autotest.step("Создаём фичи с error_repeat_count=4"):
            agent = AnalyticsAgent(config_model, db=None)
            features = SessionFeatures(**SessionFeaturesData(error_repeat_count=4).data)

        with autotest.step("Вызываем analyze_session"):
            result = agent.analyze_session(features, LearningAnalyticsConfig(error_repeat_threshold=3))

        with autotest.step("Проверяем обнаружение struggle"):
            assert_true(result.struggle_detected, "struggle обнаружен")
            assert_equal(result.struggle_type, StruggleType.REPEATING_ERRORS, "тип: repeating_errors")
            assert_equal(result.suggested_intervention, SuggestedIntervention.HINT, "интервенция: hint")

    @autotest.num("506")
    @autotest.external_id("a6b7c8d9-e0f1-4a2b-8c3d-4e5f6a7b8c9d")
    @autotest.name("AnalyticsAgent.analyze_session: обнаруживает idle")
    def test_a6b7c8d9_detects_idle(self, config_model):
        with autotest.step("Создаём фичи с idle_periods=4 и отрицательным slope"):
            agent = AnalyticsAgent(config_model, db=None)
            features = SessionFeatures(**SessionFeaturesData(idle_periods=4, action_rate_slope=-0.8).data)

        with autotest.step("Вызываем analyze_session"):
            result = agent.analyze_session(features, LearningAnalyticsConfig())

        with autotest.step("Проверяем обнаружение idle"):
            assert_true(result.struggle_detected, "struggle обнаружен")
            assert_equal(result.struggle_type, StruggleType.IDLE, "тип: idle")

    @autotest.num("507")
    @autotest.external_id("b7c8d9e0-f1a2-4b3c-9d4e-5f6a7b8c9d0e")
    @autotest.name("AnalyticsAgent.analyze_session: обнаруживает trial-and-error")
    def test_b7c8d9e0_detects_trial_and_error(self, config_model):
        with autotest.step("Создаём фичи с высокой энтропией и частотой ошибок"):
            agent = AnalyticsAgent(config_model, db=None)
            features = SessionFeatures(**SessionFeaturesData(action_sequence_entropy=0.95, error_frequency=3.0).data)

        with autotest.step("Вызываем analyze_session"):
            result = agent.analyze_session(features, LearningAnalyticsConfig())

        with autotest.step("Проверяем обнаружение trial-and-error"):
            assert_true(result.struggle_detected, "struggle обнаружен")
            assert_equal(result.struggle_type, StruggleType.TRIAL_AND_ERROR, "тип: trial_and_error")
