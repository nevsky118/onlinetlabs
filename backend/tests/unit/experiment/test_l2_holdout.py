"""L2-холдаут: effective_arm форсирует OPEN при near-transfer переносе."""
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from experiment.arm_resolver import effective_arm
from experiment.control_arm import ControlArm
from models.lab import Lab
from models.progress import LabProgress
from models.user import User

pytestmark = [pytest.mark.unit]

_SKILL = "static-ip-addressing"


@pytest.fixture
async def db_setup():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        # только нужные таблицы
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Lab.__table__.create)
        await conn.run_sync(LabProgress.__table__.create)

    async with session_factory() as db:
        # пользователь в CLOSED-плече
        db.add(User(id="u1", email="u1@test.local", control_arm="closed"))
        # L1: другая лаба того же навыка — уже пройдена
        db.add(Lab(slug="l1", title="L1", meta={"skill": _SKILL}))
        # L2: текущая лаба того же навыка — не пройдена
        db.add(Lab(slug="l2", title="L2", meta={"skill": _SKILL}))
        # лаба без навыка
        db.add(Lab(slug="no-skill", title="No skill", meta={}))
        # лаба другого навыка
        db.add(Lab(slug="other-skill", title="Other", meta={"skill": "routing"}))
        # прогресс: l1 завершена
        db.add(LabProgress(id="p1", user_id="u1", lab_slug="l1", status="completed"))
        await db.commit()

    yield session_factory
    await engine.dispose()


class TestL2Holdout:
    @autotest.num("1152")
    @autotest.external_id("cae493a7-9c3e-420c-b139-2440ee48fe63")
    @autotest.name("effective_arm: CLOSED-пользователь получает OPEN на L2-холдауте")
    async def test_cae493a7_l2_holdout_forces_open_for_closed_arm_user(self, db_setup):
        with autotest.step("Act: effective_arm для u1 на лабе l2"):
            session_factory = db_setup
            async with session_factory() as db:
                arm = await effective_arm(db, "u1", "l2")
        with autotest.step("Assert: форсируется OPEN"):
            assert_equal(arm, ControlArm.OPEN, "L2-холдаут форсирует OPEN")

    @autotest.num("1153")
    @autotest.external_id("7f79bdfe-5780-4ae5-b7a4-29f09248cb4c")
    @autotest.name("effective_arm: нет завершённой лабы того же навыка → базовое плечо")
    async def test_7f79bdfe_no_prior_completion_returns_base_arm(self, db_setup):
        with autotest.step("Arrange: u2 без прогресса"):
            session_factory = db_setup
            async with session_factory() as db:
                db.add(User(id="u2", email="u2@test.local", control_arm="closed"))
                await db.commit()
        with autotest.step("Act: effective_arm для u2 на лабе l2"):
            async with session_factory() as db:
                arm = await effective_arm(db, "u2", "l2")
        with autotest.step("Assert: базовое плечо CLOSED"):
            assert_equal(arm, ControlArm.CLOSED, "без L1 — базовое плечо")

    @autotest.num("1154")
    @autotest.external_id("9b8c58b0-ea92-4a87-8b0d-ff74718b1515")
    @autotest.name("effective_arm: другой навык — не L2-холдаут, базовое плечо")
    async def test_9b8c58b0_different_skill_returns_base_arm(self, db_setup):
        with autotest.step("Act: effective_arm для u1 на лабе other-skill"):
            session_factory = db_setup
            async with session_factory() as db:
                arm = await effective_arm(db, "u1", "other-skill")
        with autotest.step("Assert: базовое плечо CLOSED"):
            assert_equal(arm, ControlArm.CLOSED, "другой навык — не холдаут")

    @autotest.num("1155")
    @autotest.external_id("02afa4d2-f000-4d8d-bd4e-6b438700d95e")
    @autotest.name("effective_arm: лаба без skill-тега — не холдаут")
    async def test_02afa4d2_lab_without_skill_returns_base_arm(self, db_setup):
        with autotest.step("Act: effective_arm для u1 на лабе no-skill"):
            session_factory = db_setup
            async with session_factory() as db:
                arm = await effective_arm(db, "u1", "no-skill")
        with autotest.step("Assert: базовое плечо CLOSED"):
            assert_equal(arm, ControlArm.CLOSED, "лаба без навыка — не холдаут")

    @autotest.num("1156")
    @autotest.external_id("0f1a83a1-d1dc-491b-9007-4efb4687927f")
    @autotest.name("effective_arm: несуществующая лаба — не падаем, базовое плечо")
    async def test_0f1a83a1_unknown_lab_returns_base_arm(self, db_setup):
        with autotest.step("Act: effective_arm для u1 на несуществующей лабе"):
            session_factory = db_setup
            async with session_factory() as db:
                arm = await effective_arm(db, "u1", "ghost-lab")
        with autotest.step("Assert: базовое плечо CLOSED"):
            assert_equal(arm, ControlArm.CLOSED, "ghost-lab → базовое плечо")
