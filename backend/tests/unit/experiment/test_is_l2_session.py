"""is_l2_session: True when a prior lab of the same skill has been completed."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_false, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from experiment.assignment import is_l2_session
from models.catalog import Lab
from models.identity import User
from models.learning import LabProgress

pytestmark = [pytest.mark.unit]

_SKILL = "static-ip-addressing"


@pytest.fixture
async def db_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Lab.__table__.create)
        await conn.run_sync(LabProgress.__table__.create)

    async with session_factory() as db:
        db.add(User(id="u1", email="u1@test.local", control_arm="closed"))
        db.add(Lab(slug="l1", title_i18n={"en": "L1"}, meta={"skill": _SKILL}))
        db.add(Lab(slug="l2", title_i18n={"en": "L2"}, meta={"skill": _SKILL}))
        db.add(Lab(slug="no-skill", title_i18n={"en": "No skill"}, meta={}))
        db.add(Lab(slug="other-skill", title_i18n={"en": "Other"}, meta={"skill": "routing"}))
        # l1 completed by the user
        db.add(LabProgress(id="p1", user_id="u1", lab_slug="l1", status="completed"))
        await db.commit()

    yield engine, session_factory
    await engine.dispose()


class TestIsL2Session:
    @autotest.num("1182")
    @autotest.external_id("a423e1a9-6df1-460f-a0ff-a15bf16e97e1")
    @autotest.name("is_l2_session: True when a prior lab of the same skill is completed")
    async def test_a423e1a9_returns_true_when_prior_same_skill_completed(self, db_factory):
        with autotest.step("Arrange: unpack the db_factory fixture"):
            engine, session_factory = db_factory
        with autotest.step("Act: call is_l2_session for l2 with l1 completed"):
            async with session_factory() as db:
                result = await is_l2_session(db, "u1", "l2")
        with autotest.step("Assert: result is True"):
            assert_true(result is True, "a completed l1 of the same skill exists")

    @autotest.num("1183")
    @autotest.external_id("2921d28f-899c-4710-9d44-4336225cc852")
    @autotest.name("is_l2_session: False when the user has no completed labs")
    async def test_2921d28f_returns_false_when_no_prior_completion(self, db_factory):
        with autotest.step("Arrange: add user u2 with no completed labs"):
            engine, session_factory = db_factory
            async with session_factory() as db:
                db.add(User(id="u2", email="u2@test.local", control_arm="closed"))
                await db.commit()
        with autotest.step("Act: call is_l2_session for u2"):
            async with session_factory() as db:
                result = await is_l2_session(db, "u2", "l2")
        with autotest.step("Assert: result is False"):
            assert_false(result, "no completed labs → False")

    @autotest.num("1184")
    @autotest.external_id("f0ebdf40-7d24-4743-96a2-b5fd0160bf31")
    @autotest.name("is_l2_session: False when a lab of a different skill is completed")
    async def test_f0ebdf40_returns_false_for_different_skill(self, db_factory):
        with autotest.step("Arrange: unpack the db_factory fixture"):
            engine, session_factory = db_factory
        with autotest.step("Act: call is_l2_session for other-skill"):
            async with session_factory() as db:
                result = await is_l2_session(db, "u1", "other-skill")
        with autotest.step("Assert: result is False"):
            assert_false(result, "a different skill doesn't count as an L2 holdout")

    @autotest.num("1185")
    @autotest.external_id("e4278f70-b323-4cf9-bedf-83c02603247f")
    @autotest.name("is_l2_session: False for a lab without a skill tag")
    async def test_e4278f70_returns_false_for_lab_without_skill(self, db_factory):
        with autotest.step("Arrange: unpack the db_factory fixture"):
            engine, session_factory = db_factory
        with autotest.step("Act: call is_l2_session for no-skill"):
            async with session_factory() as db:
                result = await is_l2_session(db, "u1", "no-skill")
        with autotest.step("Assert: result is False"):
            assert_false(result, "a lab without a skill tag is not L2")

    @autotest.num("1186")
    @autotest.external_id("da49dbb7-4302-4578-ab26-30ec1a923cc1")
    @autotest.name("is_l2_session: False for an unknown lab, no exception")
    async def test_da49dbb7_returns_false_for_unknown_lab(self, db_factory):
        with autotest.step("Arrange: unpack the db_factory fixture"):
            engine, session_factory = db_factory
        with autotest.step("Act: call is_l2_session for ghost-lab"):
            async with session_factory() as db:
                result = await is_l2_session(db, "u1", "ghost-lab")
        with autotest.step("Assert: result is False, no crash"):
            assert_false(result, "an unknown lab returns False")
