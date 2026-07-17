import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.analytics.agent import identify_regime
from agents.analytics.models import (
    AnalyticsResult,
    SessionFeatures,
    StruggleType,
    SuggestedIntervention,
)
from config.config_model import LearningAnalyticsConfig
from tests.settings.data.analytics_data import SessionFeaturesData

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestAnalyticsAgentSession:
    @autotest.num("504")
    @autotest.external_id("ef420353-275f-4f24-afea-b6b5e442c6f9")
    @autotest.name("AnalyticsAgent.analyze_session: нет проблем в нормальной сессии")
    def test_ef420353_no_struggle_normal_session(self, config_model):
        with autotest.step("Создаём нормальные фичи"):
            features = SessionFeatures(**SessionFeaturesData().data)

        with autotest.step("Вызываем identify_regime"):
            result = identify_regime(features, LearningAnalyticsConfig())

        with autotest.step("Проверяем отсутствие struggle"):
            assert_true(isinstance(result, AnalyticsResult), f"тип: {type(result)}")
            assert_true(result.struggle_detected is False, "struggle не обнаружен")
            assert_equal(
                result.suggested_intervention, SuggestedIntervention.NONE, "нет интервенции"
            )

    @autotest.num("505")
    @autotest.external_id("2384dce9-bf9e-4ad0-af03-0cc0a0089508")
    @autotest.name("AnalyticsAgent.analyze_session: обнаруживает повторяющиеся ошибки")
    def test_2384dce9_detects_repeating_errors(self, config_model):
        with autotest.step("Создаём фичи с error_repeat_count=4"):
            features = SessionFeatures(**SessionFeaturesData(error_repeat_count=4).data)

        with autotest.step("Вызываем identify_regime"):
            result = identify_regime(features, LearningAnalyticsConfig(error_repeat_threshold=3))

        with autotest.step("Проверяем обнаружение struggle"):
            assert_true(result.struggle_detected, "struggle обнаружен")
            assert_equal(
                result.struggle_type, StruggleType.REPEATING_ERRORS, "тип: repeating_errors"
            )
            assert_equal(
                result.suggested_intervention, SuggestedIntervention.HINT, "интервенция: hint"
            )

    @autotest.num("506")
    @autotest.external_id("91e35d8d-16d1-416b-b70e-3ed64b5c36f1")
    @autotest.name("AnalyticsAgent.analyze_session: обнаруживает idle")
    def test_91e35d8d_detects_idle(self, config_model):
        with autotest.step("Создаём фичи с idle_periods=4 и отрицательным slope"):
            features = SessionFeatures(
                **SessionFeaturesData(idle_periods=4, action_rate_slope=-0.8).data
            )

        with autotest.step("Вызываем identify_regime"):
            result = identify_regime(features, LearningAnalyticsConfig())

        with autotest.step("Проверяем обнаружение idle"):
            assert_true(result.struggle_detected, "struggle обнаружен")
            assert_equal(result.struggle_type, StruggleType.IDLE, "тип: idle")

    @autotest.num("507")
    @autotest.external_id("1eb12451-0e0c-47ac-9f6b-dc13be55afb6")
    @autotest.name("AnalyticsAgent.analyze_session: обнаруживает trial-and-error")
    def test_1eb12451_detects_trial_and_error(self, config_model):
        with autotest.step("Создаём фичи с высокой энтропией и частотой ошибок"):
            features = SessionFeatures(
                **SessionFeaturesData(action_sequence_entropy=0.95, error_frequency=3.0).data
            )

        with autotest.step("Вызываем identify_regime"):
            result = identify_regime(features, LearningAnalyticsConfig())

        with autotest.step("Проверяем обнаружение trial-and-error"):
            assert_true(result.struggle_detected, "struggle обнаружен")
            assert_equal(result.struggle_type, StruggleType.TRIAL_AND_ERROR, "тип: trial_and_error")
