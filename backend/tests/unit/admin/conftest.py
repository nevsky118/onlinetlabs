"""Фикстуры in-memory SQLite для admin-тестов."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.experiment import ExperimentMetrics
from models.lab import Lab
from models.progress import LabProgress
from models.session import LearningSession
from models.user import User


async def _make_engine_and_tables():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        # SQLite не форсит FK — создаём нужные таблицы
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Lab.__table__.create)
        await conn.run_sync(LabProgress.__table__.create)
        await conn.run_sync(LearningSession.__table__.create)
        await conn.run_sync(ExperimentMetrics.__table__.create)
    return engine


@pytest.fixture
async def empty_admin_db():
    engine = await _make_engine_and_tables()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        yield db
    await engine.dispose()


@pytest.fixture
async def seeded_admin_db():
    engine = await _make_engine_and_tables()
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as db:
        db.add(
            User(id="adm-u1", email="adm@t.local", name="adm", role="student", control_arm="closed")
        )
        db.add(
            LearningSession(
                id="adm-sess-1",
                user_id="adm-u1",
                lab_slug="test-lab",
                status="ended",
            )
        )
        db.add(
            ExperimentMetrics(
                id="adm-em-1",
                session_id="adm-sess-1",
                user_id="adm-u1",
                lab_slug="test-lab",
                experiment_group="closed",
                base_arm="closed",
                total_time_seconds=1800.0,
                steps_completed=3,
                total_errors=1,
                repeated_errors=0,
                unique_error_types=1,
                interventions_received=1,
                interventions_succeeded=1,
                interventions_failed=0,
                interventions_accepted=1,
                escalations=0,
                l2_unassisted_pass=True,
                final_score=1.0,
                completed=True,
            )
        )
        await db.commit()

    async with factory() as db:
        yield db

    await engine.dispose()
