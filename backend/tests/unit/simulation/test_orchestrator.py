"""Cohort orchestrator: pool+queue, is_simulated users, policy → actor → ground-truth run."""

from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.regime_annotation import RegimeAnnotation
from models.user import User

pytestmark = [pytest.mark.unit]


async def _session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(RegimeAnnotation.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


class TestRunCohort:
    @autotest.num("2041")
    @autotest.external_id("5953d77c-c5ac-4c1d-98b6-bc2954465295")
    @autotest.name("orchestrator: пул ограничивает одновременность, юзеры is_simulated")
    async def test_5953d77c_bounded_concurrency_and_sim_users(self):
        with autotest.step("Arrange: фабрика БД, актор-мок и провижн со счётчиком пика"):
            import asyncio

            from simulation.ground_truth import record_truth
            from simulation.orchestrator import run_cohort

            factory = await _session_factory()
            actor = AsyncMock()
            peak = {"current": 0, "max": 0}

            async def provision(profile, seed, user_id):
                peak["current"] += 1
                peak["max"] = max(peak["max"], peak["current"])
                try:
                    await asyncio.sleep(0)  # yield — lets concurrency show up
                finally:
                    peak["current"] -= 1
                return f"sess-{user_id}", actor

            async def record(session_id, window, regime):
                async with factory() as db:
                    await record_truth(db, session_id, window, regime)

        with autotest.step("Act: прогоняем 6 студентов при лимите 2 одновременно"):
            report = await run_cohort(
                n=6,
                concurrency=2,
                base_seed=0,
                db_factory=factory,
                provision=provision,
                record_truth=record,
                max_steps=50,
            )

        with autotest.step("Assert: все завершены, лимит соблюдён, актор работал"):
            assert_equal(report.completed, 6, "завершено студентов")
            assert_true(report.peak_concurrency <= 2, "лимит одновременных ≤ 2")
            assert_true(actor.execute.await_count > 0, "актор исполнял действия")

        with autotest.step("Assert: юзеры помечены is_simulated, ground-truth записан"):
            async with factory() as db:
                users = (await db.execute(select(User))).scalars().all()
                truths = (await db.execute(select(RegimeAnnotation))).scalars().all()
            assert_equal(len(users), 6, "создано юзеров")
            assert_true(all(u.is_simulated for u in users), "все юзеры is_simulated")
            assert_true(len(truths) > 0, "ground-truth записан")
