"""MRT: spell lifecycle on real sqlite — exit_ts on close + censoring."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.config_model import LearningAnalyticsConfig
from learning_analytics.monitor import SessionMonitor
from models.intervention_decision import InterventionDecision

pytestmark = [pytest.mark.unit]


async def _sqlite_factory():
    # Create only the tables we need: Base.metadata.create_all fails on JSONB
    # (platform_events) under sqlite. The monitor writes ProcessStateSample (_log_process_state)
    # and BehavioralEvent (_log_would_intervene).
    from models.behavioral_event import BehavioralEvent
    from models.process_state_sample import ProcessStateSample

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(InterventionDecision.__table__.create)
        await conn.run_sync(ProcessStateSample.__table__.create)
        await conn.run_sync(BehavioralEvent.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


def _features():
    from agents.analytics.models import SessionFeatures

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
    from agents.analytics.models import (
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
    cfg.mrt_hold_probability = 1.0  # always withhold — no dispatch pulled into this test
    cfg.mrt_t_k_jitter_frac = 0.0
    m = SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=session_factory,
        orchestrator=MagicMock(),
        learning_analytics_config=cfg,
        gateway=MagicMock(),
    )
    m._session_id = "s1"
    m._user_id = "u1"
    m._lab_slug = "lab-gns3"
    m._ctx = MagicMock()
    m._session_model_id = None
    m._feature_extractor = MagicMock()
    m._feature_extractor.compute = MagicMock(return_value=_features())
    return m


class TestMRTSpellLifecycle:
    @autotest.num("1973")
    @autotest.external_id("472db8c1-dfcd-4951-bcde-0bc48220a268")
    @autotest.name(
        "MRT: смена режима на productive закрывает spell — проставляет subsequent_exit_ts"
    )
    async def test_472db8c1_spell_exit_sets_exit_ts(self):
        with autotest.step("Arrange: реальная sqlite, монитор MRT, analyze: struggle→productive"):
            sf = await _sqlite_factory()
            m = _monitor(sf)
            ev = SimpleNamespace(timestamp=datetime(2026, 6, 21, 12, 0, tzinfo=UTC))

        with autotest.step(
            "Act: цикл 1 (idle → открыть spell + записать точку), цикл 2 (productive → закрыть)"
        ):
            with (
                patch.object(m, "_load_new_events", AsyncMock(return_value=[ev])),
                patch(
                    "learning_analytics.monitor.identify_regime",
                    side_effect=[_analysis(struggle=True), _analysis(struggle=False)],
                ),
            ):
                await m._run_analysis()
                await m._run_analysis()

        with autotest.step("Assert: точка решения получила subsequent_exit_ts"):
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
            assert_equal(len(rows), 1, f"ровно 1 точка решения; получено {len(rows)}")
            assert_true(
                rows[0].subsequent_exit_ts is not None,
                "subsequent_exit_ts проставлен при закрытии spell",
            )
            assert_equal(rows[0].censored, False, "закрытая точка не censored")

    @autotest.num("1974")
    @autotest.external_id("d29b917f-ccfb-4604-a851-4c034f7e138e")
    @autotest.name("MRT censoring: end_session помечает censored открытые точки (exit_ts IS NULL)")
    async def test_d29b917f_censor_open_decisions(self):
        with autotest.step("Arrange: одна открытая точка (exit_ts null) и одна закрытая"):
            from learning_analytics.mrt import censor_open_decisions

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

        with autotest.step("Assert: открытая censored=True, закрытая нетронута, count==1"):
            assert_equal(count, 1, f"помечена 1 строка; получено {count}")
            async with sf() as db:
                opened = await db.get(InterventionDecision, "d-open")
                closed = await db.get(InterventionDecision, "d-closed")
            assert_equal(opened.censored, True, "открытая точка censored")
            assert_equal(closed.censored, False, "закрытая точка не тронута")
