"""Тесты правил детекции по прямым сигналам прогресса (Task 5)."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.analytics.agent import identify_regime
from agents.analytics.models import SessionFeatures, StruggleType, SuggestedIntervention
from config.config_model import LearningAnalyticsConfig
from tests.settings.data.analytics_data import SessionFeaturesData

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestProgressRules:
    @autotest.num("1760")
    @autotest.external_id("c8d9e0f1-a2b3-4c5d-8e6f-7a8b9c0d1e2f")
    @autotest.name("distinct_failing_actuals > threshold → TRIAL_AND_ERROR")
    def test_c8d9e0f1_distinct_actuals_triggers_trial_and_error(self, config_model):
        with autotest.step("Фичи с 3 уникальными неверными ответами (threshold=2)"):
            features = SessionFeatures(**SessionFeaturesData(distinct_failing_actuals=3).data)
            cfg = LearningAnalyticsConfig(distinct_actuals_threshold=2)

        with autotest.step("identify_regime"):
            result = identify_regime(features, cfg)

        with autotest.step("Ожидаем TRIAL_AND_ERROR + TUTOR"):
            assert_true(result.struggle_detected, "struggle обнаружен")
            assert_equal(result.struggle_type, StruggleType.TRIAL_AND_ERROR, "тип: trial_and_error")
            assert_equal(
                result.suggested_intervention, SuggestedIntervention.TUTOR, "интервенция: tutor"
            )

    @autotest.num("1761")
    @autotest.external_id("d9e0f1a2-b3c4-4d5e-9f6a-8b9c0d1e2f3a")
    @autotest.name("cycles_failing_unchanged >= threshold → STUCK_ON_STEP")
    def test_d9e0f1a2_cycles_unchanged_triggers_stuck(self, config_model):
        with autotest.step("Фичи с 3 циклами без изменений (threshold=3)"):
            features = SessionFeatures(**SessionFeaturesData(cycles_failing_unchanged=3).data)
            cfg = LearningAnalyticsConfig(unchanged_cycles_threshold=3)

        with autotest.step("identify_regime"):
            result = identify_regime(features, cfg)

        with autotest.step("Ожидаем STUCK_ON_STEP + HINT"):
            assert_true(result.struggle_detected, "struggle обнаружен")
            assert_equal(result.struggle_type, StruggleType.STUCK_ON_STEP, "тип: stuck_on_step")
            assert_equal(
                result.suggested_intervention, SuggestedIntervention.HINT, "интервенция: hint"
            )

    @autotest.num("1762")
    @autotest.external_id("e0f1a2b3-c4d5-4e6f-af7b-9c0d1e2f3a4b")
    @autotest.name("distinct_actuals confidence = min(n/4, 1.0)")
    def test_e0f1a2b3_distinct_actuals_confidence(self, config_model):
        with autotest.step("Фичи с 4 уникальными ответами"):
            features = SessionFeatures(**SessionFeaturesData(distinct_failing_actuals=4).data)
            cfg = LearningAnalyticsConfig(distinct_actuals_threshold=2)

        with autotest.step("identify_regime"):
            result = identify_regime(features, cfg)

        with autotest.step("Confidence = 1.0 при distinct_failing_actuals=4"):
            assert_equal(result.confidence, 1.0, "confidence=1.0")
