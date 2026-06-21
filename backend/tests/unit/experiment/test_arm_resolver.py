import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from experiment.arm_resolver import resolve_control_arm
from experiment.control_arm import ControlArm
from models.user import User

pytestmark = [pytest.mark.unit]


class TestArmResolver:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
        yield
        await self.engine.dispose()

    async def test_assigns_and_persists_arm_for_new_user(self):
        """Пользователь без control_arm получает плечо и оно сохраняется."""
        async with self.session_factory() as db:
            db.add(User(id="u1", email="u1@test.local"))
            await db.commit()

        async with self.session_factory() as db:
            arm = await resolve_control_arm(db, "u1")

        assert arm in (ControlArm.OPEN, ControlArm.CLOSED)

        # Проверяем персистентность
        async with self.session_factory() as db:
            arm2 = await resolve_control_arm(db, "u1")

        assert arm == arm2

    async def test_returns_existing_arm_without_reassign(self, monkeypatch):
        """Уже назначенное плечо не перезаписывается."""
        import experiment.control_arm as m
        # assign_arm никогда не должен вызываться — заставим упасть, если вызовут
        monkeypatch.setattr(m.random, "choice", lambda seq: (_ for _ in ()).throw(AssertionError("reassigned")))

        async with self.session_factory() as db:
            db.add(User(id="u2", email="u2@test.local", control_arm="closed"))
            await db.commit()

        async with self.session_factory() as db:
            arm = await resolve_control_arm(db, "u2")

        assert arm == ControlArm.CLOSED

    async def test_unknown_user_returns_arm_without_persist(self):
        """Несуществующий user_id возвращает плечо, не падает."""
        async with self.session_factory() as db:
            arm = await resolve_control_arm(db, "ghost")
        assert arm in (ControlArm.OPEN, ControlArm.CLOSED)
