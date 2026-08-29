"""MRT: spell lifecycle on real sqlite, exit_ts on close plus censoring."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from analytics.runtime.monitor import SessionMonitor
from config.config_model import LearningAnalyticsConfig
from models.research import InterventionDecision

pytestmark = [pytest.mark.unit]


async def _sqlite_factory():
    # Create only the tables we need: Base.metadata.create_all fails on JSONB
    # (platform_events) under sqlite. The monitor writes ProcessStateSample (_log_process_state)
    # and BehavioralEvent (_log_would_intervene).
    from models.research import BehavioralEvent, ProcessStateSample

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(InterventionDecision.__table__.create)
        await conn.run_sync(ProcessStateSample.__table__.create)
        await conn.run_sync(BehavioralEvent.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


def _features():
    from agents.identifier.schemas import SessionFeatures

    return SessionFeatures(
        session_id="s1",
        computed_at=datetime(2026, 6, 21, 12, 0, tzinfo=UTC),
        avg_inter_action_latency=10.0,
        action_rate_slope=0.0,
        idle_periods=1,
        total_active_time=120.0,
        time_on_current_step=60.0,
        error_repeat_count=2,
        error_repeat_rate=0.5,
        action_sequence_entropy=0.3,
        undo_redo_ratio=0.0,
        error_frequency=0.3,
        error_frequency_slope=0.0,
        unique_error_types=1,
        dominant_error=None,
        components_touched=1,
        action_diversity=0.2,
        events_total=10,
    )


def _analysis(*, struggle):
    from agents.identifier.schemas import (
        AnalyticsResult,
        DifficultyRecommendation,
        StruggleType,
        StudentMetrics,
        SuggestedIntervention,
    )

    return AnalyticsResult(
        struggle_detected=struggle,
        struggle_type=StruggleType.IDLE if struggle else None,
        confidence=0.9,
        suggested_intervention=SuggestedIntervention.HINT,
        difficulty_recommendation=DifficultyRecommendation(
            current_difficulty="beginner",
            recommended_difficulty="beginner",
            reasoning="ok",
            metrics=StudentMetrics(
                total_attempts=5, success_rate=0.6, avg_time_per_step=30.0, struggling_steps=[]
            ),
        ),
        features=_features(),
    )


def _monitor(session_factory):
    cfg = LearningAnalyticsConfig()
    cfg.dwell_thresholds = {"idle": 0.0}
    cfg.mrt_enabled = True
    cfg.mrt_hold_probability = 1.0  # always withhold, no dispatch pulled into this test
    cfg.mrt_t_k_jitter_frac = 0.0
    monitor = SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=session_factory,
        orchestrator=MagicMock(),
        learning_analytics_config=cfg,
        gateway=MagicMock(),
    )
    monitor._session_id = "s1"
    monitor._user_id = "u1"
    monitor._lab_slug = "lab-gns3"
    monitor._ctx = MagicMock()
    monitor._session_model_id = None
    monitor._feature_extractor = MagicMock()
    monitor._feature_extractor.compute = MagicMock(return_value=_features())
    return monitor


class TestMRTSpellLifecycle:
    @autotest.num("1973")
    @autotest.external_id("472db8c1-dfcd-4951-bcde-0bc48220a268")
    @autotest.name("MRT: switching regime to productive closes the spell, sets subsequent_exit_ts")
    async def test_472db8c1_spell_exit_sets_exit_ts(self):
        with autotest.step("Arrange: real sqlite, MRT monitor, analyze: struggle -> productive"):
            sf = await _sqlite_factory()
            monitor = _monitor(sf)
            ev = SimpleNamespace(timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=UTC))

        with autotest.step(
            "Act: cycle 1 (idle -> open spell + log a point), cycle 2 (productive -> close it)"
        ):
            with (
                patch.object(monitor, "_load_new_events", AsyncMock(return_value=[ev])),
                patch(
                    "analytics.runtime.monitor.identify_regime",
                    side_effect=[_analysis(struggle=True), _analysis(struggle=False)],
                ),
            ):
                await monitor._run_analysis()
                await monitor._run_analysis()

        with autotest.step("Assert: decision point got subsequent_exit_ts"):
            async with sf() as db:
                rows = (
                    (
                        await db.execute(
                            select(InterventionDecision).where(
                                InterventionDecision.session_id == "s1"
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
            assert_equal(len(rows), 1, f"exactly 1 decision point; got {len(rows)}")
            assert_true(
                rows[0].subsequent_exit_ts is not None,
                "subsequent_exit_ts is set when the spell closes",
            )
            assert_equal(rows[0].censored, False, "closed point is not censored")

    @autotest.num("1974")
    @autotest.external_id("d29b917f-ccfb-4604-a851-4c034f7e138e")
    @autotest.name("MRT censoring: end_session marks open points as censored (exit_ts IS NULL)")
    async def test_d29b917f_censor_open_decisions(self):
        with autotest.step("Arrange: one open point (exit_ts null) and one closed"):
            from analytics.runtime.mrt import censor_open_decisions

            sf = await _sqlite_factory()
            now = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
            async with sf() as db:
                db.add(
                    InterventionDecision(
                        id="d-open",
                        session_id="s1",
                        user_id="u1",
                        lab_slug="lab",
                        spell_id="sp1",
                        ts=now,
                        regime="idle",
                        dwell_seconds=10.0,
                        t_k_applied=0.0,
                        assignment="withhold",
                        subsequent_exit_ts=None,
                    )
                )
                db.add(
                    InterventionDecision(
                        id="d-closed",
                        session_id="s1",
                        user_id="u1",
                        lab_slug="lab",
                        spell_id="sp0",
                        ts=now,
                        regime="idle",
                        dwell_seconds=5.0,
                        t_k_applied=0.0,
                        assignment="intervene",
                        subsequent_exit_ts=now,
                    )
                )
                await db.commit()

        with autotest.step("Act: censor_open_decisions(s1)"):
            async with sf() as db:
                count = await censor_open_decisions(db, "s1")

        with autotest.step("Assert: open row censored=True, closed row untouched, count==1"):
            assert_equal(count, 1, f"1 row marked; got {count}")
            async with sf() as db:
                opened = await db.get(InterventionDecision, "d-open")
                closed = await db.get(InterventionDecision, "d-closed")
            assert_equal(opened.censored, True, "open point is censored")
            assert_equal(closed.censored, False, "closed point is untouched")
