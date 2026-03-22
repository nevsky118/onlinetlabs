import pytest
from datetime import datetime, timezone

from agents.analytics.models import (
    AnalyticsResult,
    DifficultyRecommendation,
    SessionFeatures,
    StudentMetrics,
    StruggleType,
    SuggestedIntervention,
)
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit, pytest.mark.agents]


def _make_features(**overrides) -> SessionFeatures:
    defaults = dict(
        avg_inter_action_latency=10.0, action_rate_slope=0.0,
        idle_periods=0, total_active_time=300.0, time_on_current_step=20.0,
        error_repeat_count=0, error_repeat_rate=0.0,
        action_sequence_entropy=0.3, undo_redo_ratio=0.0,
        error_frequency=0.0, error_frequency_slope=0.0,
        unique_error_types=0, dominant_error=None,
        components_touched=5, action_diversity=0.5, events_total=30,
        session_id="s1", computed_at=datetime.now(tz=timezone.utc),
    )
    return SessionFeatures(**(defaults | overrides))


class TestAnalyticsModels:
    @autotest.num("501")
    @autotest.external_id("b1c2d3e4-f5a6-4b7c-9d8e-f0a1b2c3d4e5")
    @autotest.name("StruggleType: значения enum")
    def test_b1c2d3e4_struggle_type_enum(self):
        with autotest.step("Проверяем значения"):
            assert_equal(StruggleType.STUCK_ON_STEP, "stuck_on_step", "stuck_on_step")
            assert_equal(StruggleType.REPEATING_ERRORS, "repeating_errors", "repeating_errors")
            assert_equal(StruggleType.IDLE, "idle", "idle")
            assert_equal(StruggleType.TRIAL_AND_ERROR, "trial_and_error", "trial_and_error")

    @autotest.num("502")
    @autotest.external_id("c2d3e4f5-a6b7-4c8d-ae9f-0a1b2c3d4e5f")
    @autotest.name("SuggestedIntervention: значения enum")
    def test_c2d3e4f5_suggested_intervention_enum(self):
        with autotest.step("Проверяем значения"):
            assert_equal(SuggestedIntervention.HINT, "hint", "hint")
            assert_equal(SuggestedIntervention.TUTOR, "tutor", "tutor")
            assert_equal(SuggestedIntervention.NONE, "none", "none")

    @autotest.num("503")
    @autotest.external_id("d3e4f5a6-b7c8-4d9e-bf0a-1b2c3d4e5f6a")
    @autotest.name("AnalyticsResult: создание с вложенными моделями")
    def test_d3e4f5a6_analytics_result(self):
        with autotest.step("Создаём SessionFeatures и DifficultyRecommendation"):
            features = _make_features()
            metrics = StudentMetrics(
                total_attempts=5, success_rate=0.8,
                avg_time_per_step=60.0, struggling_steps=[],
            )
            diff = DifficultyRecommendation(
                current_difficulty="intermediate",
                recommended_difficulty="advanced",
                reasoning="test", metrics=metrics,
            )

        with autotest.step("Создаём AnalyticsResult"):
            result = AnalyticsResult(
                difficulty_recommendation=diff,
                struggle_detected=False,
                features=features,
                confidence=0.7,
            )

        with autotest.step("Проверяем значения"):
            assert_true(result.struggle_detected is False, "struggle не обнаружен")
            assert_equal(result.suggested_intervention, SuggestedIntervention.NONE, "intervention = none")
