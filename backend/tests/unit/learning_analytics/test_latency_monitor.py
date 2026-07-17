"""Latency: врезка тайминга стадии analysis в _run_analysis (gated флагом)."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from config.config_model import LearningAnalyticsConfig
from learning_analytics.monitor import SessionMonitor

pytestmark = [pytest.mark.unit]


class _Cap:
    def __init__(self): self.added = []
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def add(self, obj): self.added.append(obj)
    async def commit(self): pass
    async def execute(self, stmt): return _Res()
    async def get(self, model, key): return None


class _Res:
    def scalar_one_or_none(self): return None
    def scalars(self): return self
    def all(self): return []


def _features():
    from agents.analytics.models import SessionFeatures
    return SessionFeatures(
        session_id="s1", computed_at=datetime(2026, 6, 21, 12, 0, tzinfo=UTC),
        avg_inter_action_latency=10.0, action_rate_slope=0.0, idle_periods=1,
        total_active_time=120.0, time_on_current_step=60.0,
        error_repeat_count=0, error_repeat_rate=0.0, action_sequence_entropy=0.3,
        undo_redo_ratio=0.0, error_frequency=0.0, error_frequency_slope=0.0,
        unique_error_types=0, dominant_error=None, components_touched=1,
        action_diversity=0.2, events_total=10,
    )


def _productive_analysis():
    from agents.analytics.models import (
        AnalyticsResult,
        DifficultyRecommendation,
        StudentMetrics,
        SuggestedIntervention,
    )
    return AnalyticsResult(
        struggle_detected=False, struggle_type=None, confidence=0.9,
        suggested_intervention=SuggestedIntervention.HINT,
        difficulty_recommendation=DifficultyRecommendation(
            current_difficulty="beginner", recommended_difficulty="beginner", reasoning="ok",
            metrics=StudentMetrics(total_attempts=5, success_rate=0.9,
                                   avg_time_per_step=30.0, struggling_steps=[]),
        ),
        features=_features(),
    )


def _monitor(cap, *, latency_enabled):
    cfg = LearningAnalyticsConfig()
    cfg.latency_capture_enabled = latency_enabled
    m = SessionMonitor(
        mcp_client=MagicMock(), db_factory=lambda: cap, orchestrator=MagicMock(),
        learning_analytics_config=cfg, gateway=MagicMock(),
    )
    m._session_id = "s1"
    m._user_id = "u1"
    m._lab_slug = "lab-gns3"
    m._ctx = MagicMock()
    m._feature_extractor = MagicMock()
    m._feature_extractor.compute = MagicMock(return_value=_features())
    return m


def _latency(cap):
    return [o for o in cap.added if type(o).__name__ == "CycleLatencySample"]


class TestLatencyMonitor:
    @autotest.num("1994")
    @autotest.external_id("40130b1d-dbd8-48d1-be6c-3b4acf4f518f")
    @autotest.name("Latency on: _run_analysis пишет сэмпл стадии analysis")
    async def test_40130b1d_records_when_enabled(self):
        with autotest.step("Arrange: монитор latency_capture_enabled=True, productive-анализ"):
            cap = _Cap()
            m = _monitor(cap, latency_enabled=True)

        with autotest.step("Act: _run_analysis с одним событием"):
            ev = SimpleNamespace(timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=UTC))
            with (
                patch.object(m, "_load_new_events", AsyncMock(return_value=[ev])),
                patch(
                    "learning_analytics.monitor.identify_regime",
                    return_value=_productive_analysis(),
                ),
            ):
                await m._run_analysis()

        with autotest.step("Assert: записан CycleLatencySample стадии analysis, duration>=0"):
            samples = _latency(cap)
            assert_equal(len(samples), 1, f"1 сэмпл латентности; получено {len(samples)}")
            assert_equal(samples[0].stage, "analysis", "стадия == analysis")
            assert_true(samples[0].duration_ms >= 0.0, "duration_ms >= 0")

    @autotest.num("1995")
    @autotest.external_id("ef99386a-699e-441b-8c8a-b6e525226c16")
    @autotest.name("Latency off: сэмплы латентности НЕ пишутся")
    async def test_ef99386a_no_record_when_disabled(self):
        with autotest.step("Arrange: монитор latency_capture_enabled=False"):
            cap = _Cap()
            m = _monitor(cap, latency_enabled=False)

        with autotest.step("Act: _run_analysis с одним событием"):
            ev = SimpleNamespace(timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=UTC))
            with (
                patch.object(m, "_load_new_events", AsyncMock(return_value=[ev])),
                patch(
                    "learning_analytics.monitor.identify_regime",
                    return_value=_productive_analysis(),
                ),
            ):
                await m._run_analysis()

        with autotest.step("Assert: ноль сэмплов латентности"):
            assert_equal(len(_latency(cap)), 0, "выключено → 0 сэмплов")
