import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in, assert_true

from experiment.arm_resolver import resolve_control_arm
from experiment.control_arm import ControlArm
from models.user import User

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
    @autotest.name("resolve_control_arm: назначает и персистирует плечо новому пользователю")
    async def test_27a29bff_assigns_and_persists_arm_for_new_user(self, db_setup):
        with autotest.step("Arrange: создать нового пользователя без control_arm"):
            session_factory = db_setup
            async with session_factory() as db:
                db.add(User(id="u1", email="u1@test.local"))
                await db.commit()

        with autotest.step("Act: resolve_control_arm для нового пользователя"):
            async with session_factory() as db:
                arm = await resolve_control_arm(db, "u1")

        with autotest.step("Assert: плечо валидно"):
            assert_in(arm, (ControlArm.OPEN, ControlArm.CLOSED), "плечо из допустимых")

        with autotest.step("Assert: плечо персистировано (повторный вызов = то же)"):
            async with session_factory() as db:
                arm2 = await resolve_control_arm(db, "u1")
            assert_equal(arm, arm2, "плечо стабильно")

    @autotest.num("1123")
    @autotest.external_id("d7dfdad5-12b9-4bd6-a6f4-1a70cdfa4192")
    @autotest.name("resolve_control_arm: существующее плечо не перезаписывается")
    async def test_d7dfdad5_returns_existing_arm_without_reassign(self, db_setup, monkeypatch):
        with autotest.step(
            "Arrange: пользователь с control_arm=closed; assign_arm → ошибка при вызове"
        ):
            session_factory = db_setup
            import experiment.control_arm as m

            monkeypatch.setattr(
                m.random, "choice", lambda seq: (_ for _ in ()).throw(AssertionError("reassigned"))
            )
            async with session_factory() as db:
                db.add(User(id="u2", email="u2@test.local", control_arm="closed"))
                await db.commit()

        with autotest.step("Act: resolve_control_arm для пользователя с existing arm"):
            async with session_factory() as db:
                arm = await resolve_control_arm(db, "u2")

        with autotest.step("Assert: вернулось CLOSED, reassign не произошёл"):
            assert_equal(arm, ControlArm.CLOSED, "existing arm не перезаписан")

    @autotest.num("1124")
    @autotest.external_id("35ec9f55-168f-483c-83c8-78a54903e2a7")
    @autotest.name("resolve_control_arm: несуществующий user_id возвращает плечо, не падает")
    async def test_35ec9f55_unknown_user_returns_arm_without_persist(self, db_setup):
        with autotest.step("Act: resolve для несуществующего пользователя"):
            session_factory = db_setup
            async with session_factory() as db:
                arm = await resolve_control_arm(db, "ghost")

        with autotest.step("Assert: плечо из допустимых"):
            assert_in(arm, (ControlArm.OPEN, ControlArm.CLOSED), "плечо валидно")
