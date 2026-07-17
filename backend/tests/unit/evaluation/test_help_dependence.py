"""#8 backend: help-dependence, dynamics of learner-initiated help requests."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.chat_message import ChatMessage

pytestmark = [pytest.mark.unit]


async def _sqlite_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(ChatMessage.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _add(db, session_id, role):
    db.add(ChatMessage(session_id=session_id, role=role, parts=[{"type": "text", "text": "?"}]))
    await db.commit()


class TestHelpDependence:
    @autotest.num("2002")
    @autotest.external_id("f4515f44-c3cf-4a72-a650-cd4f2fd9ec43")
    @autotest.name("help_dependence_count: считает только learner-сообщения (role=user)")
    async def test_f4515f44_count_user_only(self):
        with autotest.step("Arrange: 2 user + 1 assistant в s1, 1 user в s2"):
            from evaluation.help_dependence import help_dependence_count

            sf = await _sqlite_factory()
            async with sf() as db:
                await _add(db, "s1", "user")
                await _add(db, "s1", "user")
                await _add(db, "s1", "assistant")
                await _add(db, "s2", "user")

        with autotest.step("Act+Assert: s1 → 2 (assistant не считается)"):
            async with sf() as db:
                n = await help_dependence_count(db, "s1")
            assert_equal(n, 2, "только learner-запросы (role=user)")

    @autotest.num("2003")
    @autotest.external_id("3c98e905-7e3c-4e5b-ac35-6020c623ccd0")
    @autotest.name("help_dependence_trajectory: счётчики по сессиям в порядке")
    async def test_3c98e905_trajectory(self):
        with autotest.step("Arrange: s1=3 user, s2=2 user, s3=1 user"):
            from evaluation.help_dependence import help_dependence_trajectory

            sf = await _sqlite_factory()
            async with sf() as db:
                for _ in range(3):
                    await _add(db, "s1", "user")
                for _ in range(2):
                    await _add(db, "s2", "user")
                await _add(db, "s3", "user")

        with autotest.step("Act+Assert: траектория [3,2,1]"):
            async with sf() as db:
                traj = await help_dependence_trajectory(db, ["s1", "s2", "s3"])
            assert_equal(traj, [3, 2, 1], "счётчики в порядке сессий")

    @autotest.num("2004")
    @autotest.external_id("0b4ddbc5-1d38-4011-b631-2c0f5104c444")
    @autotest.name("is_declining: снижение опоры на помощь (last < first)")
    def test_0b4ddbc5_is_declining(self):
        with autotest.step("Act+Assert: чистая функция на трёх случаях"):
            from evaluation.help_dependence import is_declining

            assert_true(is_declining([3, 2, 1]), "снижается → True")
            assert_equal(is_declining([1, 2, 3]), False, "растёт → False")
            assert_equal(is_declining([2]), False, "одна точка → False")
