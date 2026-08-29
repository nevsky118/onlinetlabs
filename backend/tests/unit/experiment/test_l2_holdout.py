"""L2 holdout: effective_arm forces OPEN on near-transfer."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from experiment.assignment import ControlArm, effective_arm
from models.catalog import Lab
from models.identity import User
from models.learning import LabProgress

pytestmark = [pytest.mark.unit]

_SKILL = "static-ip-addressing"


@pytest.fixture
async def db_setup():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        # only the needed tables
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Lab.__table__.create)
        await conn.run_sync(LabProgress.__table__.create)

    async with session_factory() as db:
        # user in the CLOSED arm
        db.add(User(id="u1", email="u1@test.local", control_arm="closed"))
        # L1: another lab of the same skill, already completed
        db.add(Lab(slug="l1", title_i18n={"en": "L1"}, meta={"skill": _SKILL}))
        # L2: current lab of the same skill, not completed
        db.add(Lab(slug="l2", title_i18n={"en": "L2"}, meta={"skill": _SKILL}))
        # lab without a skill tag
        db.add(Lab(slug="no-skill", title_i18n={"en": "No skill"}, meta={}))
        # lab of a different skill
        db.add(Lab(slug="other-skill", title_i18n={"en": "Other"}, meta={"skill": "routing"}))
        # progress: l1 completed
        db.add(LabProgress(id="p1", user_id="u1", lab_slug="l1", status="completed"))
        await db.commit()

    yield session_factory
    await engine.dispose()


class TestL2Holdout:
    @autotest.num("1152")
    @autotest.external_id("cae493a7-9c3e-420c-b139-2440ee48fe63")
    @autotest.name("effective_arm: CLOSED user gets OPEN on the L2 holdout")
    async def test_cae493a7_l2_holdout_forces_open_for_closed_arm_user(self, db_setup):
        with autotest.step("Act: effective_arm for u1 on lab l2"):
            session_factory = db_setup
            async with session_factory() as db:
                arm = await effective_arm(db, "u1", "l2")
        with autotest.step("Assert: OPEN is forced"):
            assert_equal(arm, ControlArm.OPEN, "L2 holdout forces OPEN")

    @autotest.num("1153")
    @autotest.external_id("7f79bdfe-5780-4ae5-b7a4-29f09248cb4c")
    @autotest.name("effective_arm: no completed lab of the same skill → base arm")
    async def test_7f79bdfe_no_prior_completion_returns_base_arm(self, db_setup):
        with autotest.step("Arrange: u2 with no progress"):
            session_factory = db_setup
            async with session_factory() as db:
                db.add(User(id="u2", email="u2@test.local", control_arm="closed"))
                await db.commit()
        with autotest.step("Act: effective_arm for u2 on lab l2"):
            async with session_factory() as db:
                arm = await effective_arm(db, "u2", "l2")
        with autotest.step("Assert: base arm CLOSED"):
            assert_equal(arm, ControlArm.CLOSED, "no L1, base arm")

    @autotest.num("1154")
    @autotest.external_id("9b8c58b0-ea92-4a87-8b0d-ff74718b1515")
    @autotest.name("effective_arm: different skill, not an L2 holdout, base arm")
    async def test_9b8c58b0_different_skill_returns_base_arm(self, db_setup):
        with autotest.step("Act: effective_arm for u1 on lab other-skill"):
            session_factory = db_setup
            async with session_factory() as db:
                arm = await effective_arm(db, "u1", "other-skill")
        with autotest.step("Assert: base arm CLOSED"):
            assert_equal(arm, ControlArm.CLOSED, "different skill, not a holdout")

    @autotest.num("1155")
    @autotest.external_id("02afa4d2-f000-4d8d-bd4e-6b438700d95e")
    @autotest.name("effective_arm: lab without a skill tag, not a holdout")
    async def test_02afa4d2_lab_without_skill_returns_base_arm(self, db_setup):
        with autotest.step("Act: effective_arm for u1 on lab no-skill"):
            session_factory = db_setup
            async with session_factory() as db:
                arm = await effective_arm(db, "u1", "no-skill")
        with autotest.step("Assert: base arm CLOSED"):
            assert_equal(arm, ControlArm.CLOSED, "lab without a skill, not a holdout")

    @autotest.num("1156")
    @autotest.external_id("0f1a83a1-d1dc-491b-9007-4efb4687927f")
    @autotest.name("effective_arm: unknown lab, no crash, base arm")
    async def test_0f1a83a1_unknown_lab_returns_base_arm(self, db_setup):
        with autotest.step("Act: effective_arm for u1 on an unknown lab"):
            session_factory = db_setup
            async with session_factory() as db:
                arm = await effective_arm(db, "u1", "ghost-lab")
        with autotest.step("Assert: base arm CLOSED"):
            assert_equal(arm, ControlArm.CLOSED, "ghost-lab → base arm")
