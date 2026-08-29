import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from experiment.assignment import ControlArm, UserNotFound, resolve_control_arm
from models.identity import User

pytestmark = [pytest.mark.unit]


@pytest.fixture
async def db_setup():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
    yield session_factory
    await engine.dispose()


class TestArmResolver:
    @autotest.num("1122")
    @autotest.external_id("27a29bff-1945-47d3-8be5-c9cb510f89b5")
    @autotest.name("resolve_control_arm: assigns and persists the arm for a new user")
    async def test_27a29bff_assigns_and_persists_arm_for_new_user(self, db_setup):
        with autotest.step("Arrange: create a new user without control_arm"):
            session_factory = db_setup
            async with session_factory() as db:
                db.add(User(id="u1", email="u1@test.local"))
                await db.commit()

        with autotest.step("Act: resolve_control_arm for a new user"):
            async with session_factory() as db:
                arm = await resolve_control_arm(db, "u1")

        with autotest.step("Assert: arm is valid"):
            assert_in(arm, (ControlArm.OPEN, ControlArm.CLOSED), "arm is one of the valid values")

        with autotest.step("Assert: arm is persisted (repeat call = same)"):
            async with session_factory() as db:
                arm2 = await resolve_control_arm(db, "u1")
            assert_equal(arm, arm2, "arm is stable")

    @autotest.num("1123")
    @autotest.external_id("d7dfdad5-12b9-4bd6-a6f4-1a70cdfa4192")
    @autotest.name("resolve_control_arm: existing arm is not overwritten")
    async def test_d7dfdad5_returns_existing_arm_without_reassign(self, db_setup, monkeypatch):
        with autotest.step("Arrange: user with control_arm=closed; assign_arm → error if called"):
            session_factory = db_setup
            import experiment.assignment as m

            monkeypatch.setattr(
                m.random, "choice", lambda seq: (_ for _ in ()).throw(AssertionError("reassigned"))
            )
            async with session_factory() as db:
                db.add(User(id="u2", email="u2@test.local", control_arm="closed"))
                await db.commit()

        with autotest.step("Act: resolve_control_arm for a user with an existing arm"):
            async with session_factory() as db:
                arm = await resolve_control_arm(db, "u2")

        with autotest.step("Assert: returned CLOSED, no reassignment happened"):
            assert_equal(arm, ControlArm.CLOSED, "existing arm not overwritten")

    @autotest.num("1125")
    @autotest.external_id("9973c6f2-6271-423e-93ed-0febcb672226")
    @autotest.name("resolve_control_arm: unknown user_id raises UserNotFound (deterministic)")
    async def test_9973c6f2_unknown_user_raises_user_not_found(self, db_setup):
        with autotest.step("Act+Assert: resolve for an unknown user raises"):
            session_factory = db_setup
            async with session_factory() as db:
                with pytest.raises(UserNotFound):
                    await resolve_control_arm(db, "ghost")
