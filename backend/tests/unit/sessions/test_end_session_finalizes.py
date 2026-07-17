"""end_session: финализация ExperimentMetrics при завершении сессии."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_true,
    assert_equal,
    assert_is_not_none,
    assert_false,
)

from models.behavioral_event import BehavioralEvent
from models.experiment import ExperimentMetrics
from models.lab import Lab, LabStep
from models.progress import LabProgress
from models.session import LearningSession
from models.user import User
from sessions.services.lifecycle import end_session

pytestmark = [pytest.mark.unit]


@pytest.fixture
async def db_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        # отключаем FK в SQLite — таблицы создаются независимо
        await conn.execute(text("PRAGMA foreign_keys = OFF"))
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Lab.__table__.create)
        await conn.run_sync(LabStep.__table__.create)
        await conn.run_sync(LearningSession.__table__.create)
        await conn.run_sync(LabProgress.__table__.create)
        await conn.run_sync(BehavioralEvent.__table__.create)
        await conn.run_sync(ExperimentMetrics.__table__.create)

    # фикстурные данные
    async with session_factory() as db:
        db.add(
            User(id="u1", email="u1@test.local", control_arm="closed", experiment_group="group_b")
        )
        db.add(Lab(slug="lab-a", title="Lab A", meta={"skill": "routing"}))
        db.add(LabStep(lab_slug="lab-a", step_order=1, slug="step-1", title="Step 1"))
        db.add(LabStep(lab_slug="lab-a", step_order=2, slug="step-2", title="Step 2"))
        db.add(
            LearningSession(
                id="sess-1",
                user_id="u1",
                lab_slug="lab-a",
                status="active",
                started_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            )
        )
        db.add(
            LabProgress(
                id="lp1", user_id="u1", lab_slug="lab-a", status="in_progress", current_step=1
            )
        )
        # 1 интервенция, 1 ошибка
        db.add(
            BehavioralEvent(
                id="ev1",
                session_id="sess-1",
                user_id="u1",
                lab_slug="lab-a",
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=20),
                event_type="intervention",
                action="hint",
                success=True,
            )
        )
        db.add(
            BehavioralEvent(
                id="ev2",
                session_id="sess-1",
                user_id="u1",
                lab_slug="lab-a",
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=10),
                event_type="error",
                action="err",
                success=False,
                message="timeout",
            )
        )
        await db.commit()

    yield engine, session_factory
    await engine.dispose()


class TestEndSessionFinalizes:
    @autotest.num("1302")
    @autotest.external_id("9c5b5efc-c9a0-4d89-9508-196d8785783f")
    @autotest.name("end_session: создаёт строку ExperimentMetrics с корректными полями")
    async def test_9c5b5efc_inserts_experiment_metrics_row(self, db_factory):
        engine, session_factory = db_factory
        with autotest.step("Act: вызов end_session"):
            async with session_factory() as db:
                result = await end_session(db, "sess-1", "u1", "ended")
        with autotest.step("Assert: сессия завершена и статус корректен"):
            assert_is_not_none(result, "результат не None")
            assert_equal(result.status, "ended", "статус = ended")
        with autotest.step("Assert: строка ExperimentMetrics создана с правильными полями"):
            async with session_factory() as db:
                rows = (
                    (
                        await db.execute(
                            select(ExperimentMetrics).where(
                                ExperimentMetrics.session_id == "sess-1"
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
            assert_equal(len(rows), 1, "ровно одна строка метрик")
            m = rows[0]
            assert_equal(m.session_id, "sess-1", "session_id")
            assert_equal(m.user_id, "u1", "user_id")
            assert_equal(m.lab_slug, "lab-a", "lab_slug")
            assert_equal(m.experiment_group, "group_b", "experiment_group")
            # control_arm = effective arm сессии (L1 → совпадает с training arm)
            assert_equal(m.control_arm, "closed", "control_arm = closed")
            # base_arm = постоянный training-arm пользователя (User.control_arm)
            assert_equal(m.base_arm, "closed", "base_arm = closed")
            assert_equal(m.interventions_received, 1, "1 интервенция")
            assert_equal(m.total_errors, 1, "1 ошибка")
            assert_true(m.total_time_seconds > 0, "total_time_seconds > 0")
            # current_step=1 из 2 (LabStep fallback, спека отсутствует) → не завершено
            assert_false(m.completed, "не завершено")

    @autotest.num("1303")
    @autotest.external_id("4750257f-ef70-4e5b-8b1d-e6c106b90512")
    @autotest.name("end_session: ошибка финализации не ломает завершение сессии")
    async def test_4750257f_finalization_failure_does_not_break_end_session(
        self, db_factory, monkeypatch
    ):
        engine, session_factory = db_factory
        with autotest.step("Arrange: патчим _finalize_experiment_metrics на исключение"):
            import sessions.services.lifecycle as lc

            async def _boom(*args, **kwargs):
                raise RuntimeError("финализация упала")

            monkeypatch.setattr(lc, "_finalize_experiment_metrics", _boom)
        with autotest.step("Act: вызов end_session несмотря на падение финализации"):
            async with session_factory() as db:
                session = await end_session(db, "sess-1", "u1", "ended")
        with autotest.step("Assert: сессия завершилась корректно"):
            assert_is_not_none(session, "сессия не None")
            assert_equal(session.status, "ended", "статус = ended")
            assert_is_not_none(session.ended_at, "ended_at проставлен")
