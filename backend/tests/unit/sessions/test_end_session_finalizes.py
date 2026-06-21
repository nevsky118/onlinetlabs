"""end_session: финализация ExperimentMetrics при завершении сессии."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.behavioral_event import BehavioralEvent
from models.experiment import ExperimentMetrics
from models.lab import Lab, LabStep
from models.progress import LabProgress
from models.session import LearningSession
from models.user import User
from sessions.services.lifecycle import end_session

pytestmark = [pytest.mark.unit]


class TestEndSessionFinalizes:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            # без строгих FK в SQLite
        )
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

        async with self.engine.begin() as conn:
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
        async with self.session_factory() as db:
            db.add(User(id="u1", email="u1@test.local", control_arm="closed", experiment_group="group_b"))
            db.add(Lab(slug="lab-a", title="Lab A", meta={"skill": "routing"}))
            db.add(LabStep(lab_slug="lab-a", step_order=1, slug="step-1", title="Step 1"))
            db.add(LabStep(lab_slug="lab-a", step_order=2, slug="step-2", title="Step 2"))
            db.add(LearningSession(
                id="sess-1",
                user_id="u1",
                lab_slug="lab-a",
                status="active",
                started_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            ))
            db.add(LabProgress(id="lp1", user_id="u1", lab_slug="lab-a", status="in_progress", current_step=1))
            # 1 интервенция, 1 ошибка
            db.add(BehavioralEvent(
                id="ev1", session_id="sess-1", user_id="u1", lab_slug="lab-a",
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=20),
                event_type="intervention", action="hint", success=True,
            ))
            db.add(BehavioralEvent(
                id="ev2", session_id="sess-1", user_id="u1", lab_slug="lab-a",
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=10),
                event_type="error", action="err", success=False, message="timeout",
            ))
            await db.commit()

        yield
        await self.engine.dispose()

    async def test_inserts_experiment_metrics_row(self):
        """end_session создаёт строку ExperimentMetrics с корректными полями."""
        async with self.session_factory() as db:
            result = await end_session(db, "sess-1", "u1", "ended")

        assert result is not None
        assert result.status == "ended"

        async with self.session_factory() as db:
            rows = (await db.execute(
                select(ExperimentMetrics).where(ExperimentMetrics.session_id == "sess-1")
            )).scalars().all()

        assert len(rows) == 1
        m = rows[0]
        assert m.session_id == "sess-1"
        assert m.user_id == "u1"
        assert m.lab_slug == "lab-a"
        assert m.experiment_group == "group_b"
        # control_arm = effective arm сессии (L1 → совпадает с training arm)
        assert m.control_arm == "closed"
        # base_arm = постоянный training-arm пользователя (User.control_arm)
        assert m.base_arm == "closed"
        assert m.interventions_received == 1
        assert m.total_errors == 1
        assert m.total_time_seconds > 0
        # current_step=1 из 2 (LabStep fallback, спека отсутствует) → не завершено
        assert m.completed is False

    async def test_finalization_failure_does_not_break_end_session(self, monkeypatch):
        """Ошибка финализации не ломает завершение сессии."""
        import sessions.services.lifecycle as lc

        async def _boom(*args, **kwargs):
            raise RuntimeError("финализация упала")

        monkeypatch.setattr(lc, "_finalize_experiment_metrics", _boom)

        async with self.session_factory() as db:
            session = await end_session(db, "sess-1", "u1", "ended")

        # сессия завершилась несмотря на ошибку финализации
        assert session is not None
        assert session.status == "ended"
        assert session.ended_at is not None
