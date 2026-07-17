"""is_l2_session: True при предшествующей завершённой лабе того же навыка."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_true, assert_false

from experiment.arm_resolver import is_l2_session
from models.lab import Lab
from models.progress import LabProgress
from models.user import User

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
        db.add(Lab(slug="l1", title="L1", meta={"skill": _SKILL}))
        db.add(Lab(slug="l2", title="L2", meta={"skill": _SKILL}))
        db.add(Lab(slug="no-skill", title="No skill", meta={}))
        db.add(Lab(slug="other-skill", title="Other", meta={"skill": "routing"}))
        # l1 завершена пользователем
        db.add(LabProgress(id="p1", user_id="u1", lab_slug="l1", status="completed"))
        await db.commit()

    yield engine, session_factory
    await engine.dispose()


class TestIsL2Session:
    @autotest.num("1182")
    @autotest.external_id("a423e1a9-6df1-460f-a0ff-a15bf16e97e1")
    @autotest.name("is_l2_session: True когда есть пройденная лаба того же навыка")
    async def test_a423e1a9_returns_true_when_prior_same_skill_completed(self, db_factory):
        engine, session_factory = db_factory
        with autotest.step("Act: вызов is_l2_session для l2 с завершённой l1"):
            async with session_factory() as db:
                result = await is_l2_session(db, "u1", "l2")
        with autotest.step("Assert: результат True"):
            assert_true(result is True, "есть завершённая l1 того же навыка")

    @autotest.num("1183")
    @autotest.external_id("2921d28f-899c-4710-9d44-4336225cc852")
    @autotest.name("is_l2_session: False когда нет завершённых лаб у пользователя")
    async def test_2921d28f_returns_false_when_no_prior_completion(self, db_factory):
        engine, session_factory = db_factory
        with autotest.step("Arrange: добавляем пользователя u2 без завершённых лаб"):
            async with session_factory() as db:
                db.add(User(id="u2", email="u2@test.local", control_arm="closed"))
                await db.commit()
        with autotest.step("Act: вызов is_l2_session для u2"):
            async with session_factory() as db:
                result = await is_l2_session(db, "u2", "l2")
        with autotest.step("Assert: результат False"):
            assert_false(result, "нет завершённых лаб → False")

    @autotest.num("1184")
    @autotest.external_id("f0ebdf40-7d24-4743-96a2-b5fd0160bf31")
    @autotest.name("is_l2_session: False когда завершена лаба другого навыка")
    async def test_f0ebdf40_returns_false_for_different_skill(self, db_factory):
        engine, session_factory = db_factory
        with autotest.step("Act: вызов is_l2_session для other-skill"):
            async with session_factory() as db:
                result = await is_l2_session(db, "u1", "other-skill")
        with autotest.step("Assert: результат False"):
            assert_false(result, "другой навык не считается L2-холдаутом")

    @autotest.num("1185")
    @autotest.external_id("e4278f70-b323-4cf9-bedf-83c02603247f")
    @autotest.name("is_l2_session: False для лабы без skill-тега")
    async def test_e4278f70_returns_false_for_lab_without_skill(self, db_factory):
        engine, session_factory = db_factory
        with autotest.step("Act: вызов is_l2_session для no-skill"):
            async with session_factory() as db:
                result = await is_l2_session(db, "u1", "no-skill")
        with autotest.step("Assert: результат False"):
            assert_false(result, "лаба без skill-тега не является L2")

    @autotest.num("1186")
    @autotest.external_id("da49dbb7-4302-4578-ab26-30ec1a923cc1")
    @autotest.name("is_l2_session: False для несуществующей лабы, без исключения")
    async def test_da49dbb7_returns_false_for_unknown_lab(self, db_factory):
        engine, session_factory = db_factory
        with autotest.step("Act: вызов is_l2_session для ghost-lab"):
            async with session_factory() as db:
                result = await is_l2_session(db, "u1", "ghost-lab")
        with autotest.step("Assert: результат False, не падает"):
            assert_false(result, "несуществующая лаба возвращает False")
