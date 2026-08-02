import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.identifier.models import (
    AnalyticsResult,
    DifficultyRecommendation,
    SessionFeatures,
    StruggleType,
    StudentMetrics,
    SuggestedIntervention,
)
from tests.settings.data.analytics_data import SessionFeaturesData

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestAnalyticsModels:
    @autotest.num("501")
    @autotest.external_id("9b4885ec-a76d-4fc9-bfd3-3892d52af032")
    @autotest.name("StruggleType: enum values")
    def test_9b4885ec_struggle_type_enum(self):
        with autotest.step("Assert values"):
            assert_equal(StruggleType.STUCK_ON_STEP, "stuck_on_step", "stuck_on_step")
            assert_equal(StruggleType.REPEATING_ERRORS, "repeating_errors", "repeating_errors")
            assert_equal(StruggleType.IDLE, "idle", "idle")
            assert_equal(StruggleType.TRIAL_AND_ERROR, "trial_and_error", "trial_and_error")

    @autotest.num("502")
    @autotest.external_id("c8035b51-488a-43e4-924b-bfcb8272bcd9")
    @autotest.name("SuggestedIntervention: enum values")
    def test_c8035b51_suggested_intervention_enum(self):
        with autotest.step("Assert values"):
            assert_equal(SuggestedIntervention.HINT, "hint", "hint")
            assert_equal(SuggestedIntervention.TUTOR, "tutor", "tutor")
            assert_equal(SuggestedIntervention.NONE, "none", "none")

    @autotest.num("503")
    @autotest.external_id("df481cf6-81b5-4a4e-b29c-2cc53240b432")
    @autotest.name("AnalyticsResult: construction with nested models")
    def test_df481cf6_analytics_result(self):
        with autotest.step("Create SessionFeatures and DifficultyRecommendation"):
            features = SessionFeatures(**SessionFeaturesData().data)
            metrics = StudentMetrics(
                total_attempts=5,
                success_rate=0.8,
                avg_time_per_step=60.0,
                struggling_steps=[],
            )
            diff = DifficultyRecommendation(
                current_difficulty="intermediate",
                recommended_difficulty="advanced",
                reasoning="test",
                metrics=metrics,
            )

        with autotest.step("Create AnalyticsResult"):
            result = AnalyticsResult(
                difficulty_recommendation=diff,
                struggle_detected=False,
                features=features,
                confidence=0.7,
            )

        with autotest.step("Assert values"):
            assert_true(result.struggle_detected is False, "struggle not detected")
            assert_equal(
                result.suggested_intervention, SuggestedIntervention.NONE, "intervention = none"
            )
