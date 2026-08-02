import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.identifier.agent import identify_regime
from agents.identifier.models import (
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
    @autotest.name("AnalyticsAgent.analyze_session: no issues in a normal session")
    def test_ef420353_no_struggle_normal_session(self, config_model):
        with autotest.step("Create normal features"):
            features = SessionFeatures(**SessionFeaturesData().data)

        with autotest.step("Call identify_regime"):
            result = identify_regime(features, LearningAnalyticsConfig())

        with autotest.step("Assert no struggle"):
            assert_true(isinstance(result, AnalyticsResult), f"type: {type(result)}")
            assert_true(result.struggle_detected is False, "struggle not detected")
            assert_equal(
                result.suggested_intervention, SuggestedIntervention.NONE, "no intervention"
            )

    @autotest.num("505")
    @autotest.external_id("2384dce9-bf9e-4ad0-af03-0cc0a0089508")
    @autotest.name("AnalyticsAgent.analyze_session: detects repeating errors")
    def test_2384dce9_detects_repeating_errors(self, config_model):
        with autotest.step("Create features with error_repeat_count=4"):
            features = SessionFeatures(**SessionFeaturesData(error_repeat_count=4).data)

        with autotest.step("Call identify_regime"):
            result = identify_regime(features, LearningAnalyticsConfig(error_repeat_threshold=3))

        with autotest.step("Assert struggle is detected"):
            assert_true(result.struggle_detected, "struggle detected")
            assert_equal(
                result.struggle_type, StruggleType.REPEATING_ERRORS, "type: repeating_errors"
            )
            assert_equal(
                result.suggested_intervention, SuggestedIntervention.HINT, "intervention: hint"
            )

    @autotest.num("506")
    @autotest.external_id("91e35d8d-16d1-416b-b70e-3ed64b5c36f1")
    @autotest.name("AnalyticsAgent.analyze_session: detects idle")
    def test_91e35d8d_detects_idle(self, config_model):
        with autotest.step("Create features with idle_periods=4 and negative slope"):
            features = SessionFeatures(
                **SessionFeaturesData(idle_periods=4, action_rate_slope=-0.8).data
            )

        with autotest.step("Call identify_regime"):
            result = identify_regime(features, LearningAnalyticsConfig())

        with autotest.step("Assert idle is detected"):
            assert_true(result.struggle_detected, "struggle detected")
            assert_equal(result.struggle_type, StruggleType.IDLE, "type: idle")

    @autotest.num("507")
    @autotest.external_id("1eb12451-0e0c-47ac-9f6b-dc13be55afb6")
    @autotest.name("AnalyticsAgent.analyze_session: detects trial-and-error")
    def test_1eb12451_detects_trial_and_error(self, config_model):
        with autotest.step("Create features with high entropy and error frequency"):
            features = SessionFeatures(
                **SessionFeaturesData(action_sequence_entropy=0.95, error_frequency=3.0).data
            )

        with autotest.step("Call identify_regime"):
            result = identify_regime(features, LearningAnalyticsConfig())

        with autotest.step("Assert trial-and-error is detected"):
            assert_true(result.struggle_detected, "struggle detected")
            assert_equal(
                result.struggle_type, StruggleType.TRIAL_AND_ERROR, "type: trial_and_error"
            )
