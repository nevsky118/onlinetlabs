"""Cohort orchestrator: pool+queue, is_simulated users, policy → actor → ground-truth run."""

from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.identity import User
from models.research import RegimeAnnotation

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
    @autotest.name("orchestrator: pool bounds concurrency, users flagged is_simulated")
    async def test_5953d77c_bounded_concurrency_and_sim_users(self):
        with autotest.step("Arrange: DB factory, mock actor, and provision with a peak counter"):
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
                    await asyncio.sleep(0)  # yield so concurrency can show up
                finally:
                    peak["current"] -= 1
                return f"sess-{user_id}", actor

            async def record(session_id, window, regime):
                async with factory() as db:
                    await record_truth(db, session_id, window, regime)

        with autotest.step("Act: run 6 students with a concurrency limit of 2"):
            report = await run_cohort(
                n=6,
                concurrency=2,
                base_seed=0,
                db_factory=factory,
                provision=provision,
                record_truth=record,
                max_steps=50,
            )

        with autotest.step("Assert: all completed, limit held, actor ran"):
            assert_equal(report.completed, 6, "students completed")
            assert_true(report.peak_concurrency <= 2, "concurrency limit ≤ 2")
            assert_true(actor.execute.await_count > 0, "actor executed actions")

        with autotest.step("Assert: users flagged is_simulated, ground truth recorded"):
            async with factory() as db:
                users = (await db.execute(select(User))).scalars().all()
                truths = (await db.execute(select(RegimeAnnotation))).scalars().all()
            assert_equal(len(users), 6, "users created")
            assert_true(all(user.is_simulated for user in users), "all users is_simulated")
            assert_true(len(truths) > 0, "ground truth recorded")
