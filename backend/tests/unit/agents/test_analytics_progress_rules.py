"""Tests for detection rules based on direct progress signals (Task 5)."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.identifier.agent import identify_regime
from agents.identifier.schemas import SessionFeatures, StruggleType, SuggestedIntervention
from config.config_model import LearningAnalyticsConfig
from tests.settings.data.analytics_data import SessionFeaturesData

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestProgressRules:
    @autotest.num("2604")
    @autotest.external_id("5e39ad8c-79b6-46ed-a2e0-d7f0971281ed")
    @autotest.name("distinct_failing_actuals > threshold → TRIAL_AND_ERROR")
    def test_5e39ad8c_distinct_actuals_triggers_trial_and_error(self, config_model):
        with autotest.step("Features with 3 distinct incorrect answers (threshold=2)"):
            features = SessionFeatures(**SessionFeaturesData(distinct_failing_actuals=3).data)
            cfg = LearningAnalyticsConfig(distinct_actuals_threshold=2)

        with autotest.step("identify_regime"):
            result = identify_regime(features, cfg)

        with autotest.step("Expect TRIAL_AND_ERROR + TUTOR"):
            assert_true(result.struggle_detected, "struggle detected")
            assert_equal(
                result.struggle_type, StruggleType.TRIAL_AND_ERROR, "type: trial_and_error"
            )
            assert_equal(
                result.suggested_intervention, SuggestedIntervention.TUTOR, "intervention: tutor"
            )

    @autotest.num("1761")
    @autotest.external_id("1aca0987-e7bf-439d-9c36-8a43bc54093b")
    @autotest.name("cycles_failing_unchanged >= threshold → STUCK_ON_STEP")
    def test_1aca0987_cycles_unchanged_triggers_stuck(self, config_model):
        with autotest.step("Features with 3 unchanged cycles (threshold=3)"):
            features = SessionFeatures(**SessionFeaturesData(cycles_failing_unchanged=3).data)
            cfg = LearningAnalyticsConfig(unchanged_cycles_threshold=3)

        with autotest.step("identify_regime"):
            result = identify_regime(features, cfg)

        with autotest.step("Expect STUCK_ON_STEP + HINT"):
            assert_true(result.struggle_detected, "struggle detected")
            assert_equal(result.struggle_type, StruggleType.STUCK_ON_STEP, "type: stuck_on_step")
            assert_equal(
                result.suggested_intervention, SuggestedIntervention.HINT, "intervention: hint"
            )

    @autotest.num("1762")
    @autotest.external_id("e0f1a2b3-c4d5-4e6f-af7b-9c0d1e2f3a4b")
    @autotest.name("distinct_actuals confidence = min(n/4, 1.0)")
    def test_e0f1a2b3_distinct_actuals_confidence(self, config_model):
        with autotest.step("Features with 4 distinct answers"):
            features = SessionFeatures(**SessionFeaturesData(distinct_failing_actuals=4).data)
            cfg = LearningAnalyticsConfig(distinct_actuals_threshold=2)

        with autotest.step("identify_regime"):
            result = identify_regime(features, cfg)

        with autotest.step("Confidence = 1.0 when distinct_failing_actuals=4"):
            assert_equal(result.confidence, 1.0, "confidence=1.0")
