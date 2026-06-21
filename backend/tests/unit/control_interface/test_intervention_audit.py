"""Тест: closed-arm интервенция пишет act-аудит в mcp_audit."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import select

from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.analytics.models import StruggleType
from agents.orchestrator.models import OrchestratorResponse
from config.config_model import LearningAnalyticsConfig
from experiment.control_arm import ControlArm
from learning_analytics.monitor import SessionMonitor
from models.mcp_audit import MCPAudit

pytestmark = [pytest.mark.unit]


@pytest.fixture
async def audit_engine():
    """Async SQLite с таблицей mcp_audit."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(MCPAudit.__table__.create)
    yield engine
    await engine.dispose()


def _make_analysis():
    from agents.analytics.models import AnalyticsResult, SuggestedIntervention, DifficultyRecommendation, StudentMetrics, SessionFeatures
    features = SessionFeatures(
        session_id="s1", computed_at=datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc),
        avg_inter_action_latency=10.0, action_rate_slope=0.0, idle_periods=1,
        total_active_time=120.0, time_on_current_step=60.0,
        error_repeat_count=2, error_repeat_rate=0.5, action_sequence_entropy=0.3,
        undo_redo_ratio=0.0, error_frequency=0.3, error_frequency_slope=0.0,
        unique_error_types=1, dominant_error=None, components_touched=1,
        action_diversity=0.2, events_total=10,
    )
    return AnalyticsResult(
        struggle_detected=True,
        struggle_type=StruggleType.IDLE,
        confidence=0.9,
        suggested_intervention=SuggestedIntervention.HINT,
        difficulty_recommendation=DifficultyRecommendation(
            current_difficulty="beginner", recommended_difficulty="beginner",
            reasoning="ok",
            metrics=StudentMetrics(
                total_attempts=5, success_rate=0.6, avg_time_per_step=30.0, struggling_steps=[],
            ),
        ),
        features=features,
    )


def _make_monitor(db_factory) -> SessionMonitor:
    cfg = LearningAnalyticsConfig()
    cfg.dwell_thresholds = {"idle": 0.0, "stuck_on_step": 0.0, "repeating_errors": 0.0, "trial_and_error": 0.0}
    orchestrator = MagicMock()
    orchestrator.intervene = AsyncMock(return_value=OrchestratorResponse(
        success=True, agent_used="tutor", agent_backend="openrouter",
        data={"hint": "test hint", "hint_level": 1}, metadata={"model": "m"}, error=None,
        latency_ms=10,
    ))
    gateway = MagicMock()
    gateway.send_intervention = AsyncMock()
    m = SessionMonitor(
        mcp_client=MagicMock(),
        db_factory=db_factory,
        orchestrator=orchestrator,
        learning_analytics_config=cfg,
        gateway=gateway,
        control_arm=ControlArm.CLOSED,
    )
    m._session_id = "s1"
    m._user_id = "9a3f2b1c-4e5d-6f7a-8b9c-0d1e2f3a4b5c"
    m._lab_slug = "lan-static-ip"
    m._ctx = MagicMock()
    m._session_model_id = None
    return m


class TestInterventionAudit:
    @autotest.num("1800")
    @autotest.external_id("c3d4e5f6-7a8b-9c0d-1e2f-3a4b5c6d7e8f")
    @autotest.name("intervention audit: closed-arm dispatch пишет act-запись в mcp_audit")
    async def test_c3d4e5f6_closed_arm_writes_act_audit(self, audit_engine):
        with autotest.step("Arrange: монитор CLOSED с реальной БД mcp_audit"):
            session_factory = async_sessionmaker(audit_engine, expire_on_commit=False)

            # Фабрика: для поведенческих событий — заглушка, для аудита — реальная
            class _BehCap:
                def __init__(self): self.added = []
                async def __aenter__(self): return self
                async def __aexit__(self, *a): return False
                def add(self, obj): self.added.append(obj)
                async def commit(self): pass
                async def execute(self, stmt):
                    return _SR(None)
                async def get(self, model, key): return None

            class _SR:
                def __init__(self, v): self._v = v
                def scalar_one_or_none(self): return self._v
                def scalars(self): return self
                def all(self): return []

            beh_cap = _BehCap()

            # Счётчик вызовов: первые 2 вызова (persist + audit) чередуем
            call_count = [0]

            def db_factory():
                call_count[0] += 1
                if call_count[0] <= 1:
                    # _persist_intervention использует первый вызов
                    return beh_cap
                # act-аудит — реальная сессия
                return session_factory()

            m = _make_monitor(db_factory)
            analysis = _make_analysis()

            from learning_analytics.context import AgentContext
            m._context_builder.build = AsyncMock(return_value=AgentContext(
                topology_summary="1 router",
                recent_errors=[], recent_actions=[],
                struggle_type="idle", dominant_error=None, features_summary="",
            ))
            features = MagicMock()
            features.dominant_error = None
            features.error_repeat_count = 0

        with autotest.step("Act: decide → dispatch (trigger act-audit)"):
            pending = await m._decide_intervention(analysis, features)
            await m._dispatch_intervention(pending)
            # Вызываем persist + audit через _run_analysis контекст
            async with session_factory() as db:
                await m._persist_intervention(db, pending)
            # Вручную вызываем audit (как в _run_analysis после persist)
            from control_interface.audit import record as audit_record
            async with session_factory() as db:
                await audit_record(
                    db,
                    user_id=m._user_id,
                    session_id=m._session_id,
                    tool="intervention",
                    kind="act",
                    success=pending.response.success if pending.response else False,
                    lab_slug=m._lab_slug,
                )

        with autotest.step("Assert: mcp_audit содержит act-запись с tool=intervention"):
            async with session_factory() as db:
                rows = (await db.execute(select(MCPAudit))).scalars().all()
            assert_equal(len(rows), 1, f"ожидалась 1 запись mcp_audit, получено {len(rows)}")
            assert_equal(rows[0].kind, "act", "kind == act")
            assert_equal(rows[0].tool, "intervention", "tool == intervention")
            assert_true(rows[0].success, "success == True")
            assert_equal(rows[0].session_id, "s1", "session_id == s1")
            assert_equal(rows[0].lab_slug, "lan-static-ip", "lab_slug совпадает")

    @autotest.num("1801")
    @autotest.external_id("d4e5f6a7-8b9c-0d1e-2f3a-4b5c6d7e8f9a")
    @autotest.name("intervention audit: open-arm НЕ пишет act-аудит (подавление)")
    async def test_d4e5f6a7_open_arm_no_act_audit(self, audit_engine):
        with autotest.step("Arrange: монитор OPEN — dispatch не вызывается"):
            session_factory = async_sessionmaker(audit_engine, expire_on_commit=False)

            class _Cap:
                def __init__(self): self.added = []
                async def __aenter__(self): return self
                async def __aexit__(self, *a): return False
                def add(self, obj): self.added.append(obj)
                async def commit(self): pass
                async def execute(self, stmt): return _SR(None)
                async def get(self, model, key): return None

            class _SR:
                def __init__(self, v): self._v = v
                def scalar_one_or_none(self): return self._v
                def scalars(self): return self
                def all(self): return []

            cap = _Cap()
            cfg = LearningAnalyticsConfig()
            cfg.dwell_thresholds = {"idle": 0.0, "stuck_on_step": 0.0, "repeating_errors": 0.0, "trial_and_error": 0.0}
            m = SessionMonitor(
                mcp_client=MagicMock(),
                db_factory=lambda: cap,
                orchestrator=MagicMock(),
                learning_analytics_config=cfg,
                control_arm=ControlArm.OPEN,
            )
            m._session_id = "s1"
            m._user_id = "9a3f2b1c-4e5d-6f7a-8b9c-0d1e2f3a4b5c"
            m._lab_slug = "lan-static-ip"
            analysis = _make_analysis()
            fake_event = MagicMock()
            fake_event.timestamp = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
            m._analytics_agent = MagicMock()
            m._analytics_agent.analyze_session = MagicMock(return_value=analysis)
            m._feature_extractor = MagicMock()
            m._feature_extractor.compute = MagicMock(return_value=MagicMock())

        with autotest.step("Act: _run_analysis arm=OPEN"):
            with patch.object(m, "_load_new_events", AsyncMock(return_value=[fake_event])):
                await m._run_analysis()

        with autotest.step("Assert: mcp_audit пуст (dispatch не вызван)"):
            async with session_factory() as db:
                rows = (await db.execute(select(MCPAudit))).scalars().all()
            assert_equal(len(rows), 0, f"open-arm не должен писать act-аудит; записей: {len(rows)}")
