import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from experiment.group_assigner import ExperimentGroup
from models import Base
from models.lab import Lab
from models.session import LearningSession
from models.user import User
from sessions import service

pytestmark = [pytest.mark.unit]


class TestSessionService:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        await self.engine.dispose()

    async def _create_user_and_lab(self, user_id: str, experiment_group: str | None):
        async with self.session_factory() as db:
            user = User(
                id=user_id,
                name="Student",
                email=f"{user_id}@test.local",
                experiment_group=experiment_group,
            )
            lab = Lab(slug="ospf-vlan-lab", title="OSPF VLAN Lab")
            db.add_all([user, lab])
            await db.commit()

    async def _get_user(self, user_id: str) -> User:
        async with self.session_factory() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one()

    async def _get_learning_session(self, session_id: str) -> LearningSession:
        async with self.session_factory() as db:
            result = await db.execute(
                select(LearningSession).where(LearningSession.id == session_id)
            )
            return result.scalar_one()

    @autotest.num("650")
    @autotest.external_id("7bc8fd0e-1aa4-4f46-a443-bcf1928a2ca8")
    @autotest.name("create_session: назначает группу новому участнику")
    async def test_7bc8fd0e_create_session_assigns_group(self, monkeypatch):
        # Arrange
        with autotest.step("Готовим пользователя без experiment_group в БД"):
            await self._create_user_and_lab("u1", experiment_group=None)
            monkeypatch.setattr(
                service,
                "assign_group",
                lambda: ExperimentGroup.GROUP_B,
            )

        # Act
        with autotest.step("Создаём учебную сессию"):
            async with self.session_factory() as db:
                session = await service.create_session(db, "u1", "ospf-vlan-lab")

        # Assert
        with autotest.step("Проверяем сохранённую группу пользователя"):
            user = await self._get_user("u1")
            assert_equal(user.experiment_group, "group_b", "experiment_group")

        with autotest.step("Проверяем сохранённую учебную сессию"):
            saved_session = await self._get_learning_session(session.id)
            assert_equal(saved_session.user_id, "u1", "user_id")
            assert_equal(saved_session.lab_slug, "ospf-vlan-lab", "lab_slug")
            assert_equal(saved_session.status, "active", "status")

    @autotest.num("651")
    @autotest.external_id("a0d67028-622f-48b0-8380-73e4c86b06fb")
    @autotest.name("create_session: сохраняет существующую группу")
    async def test_a0d67028_create_session_keeps_existing_group(self, monkeypatch):
        # Arrange
        with autotest.step("Готовим пользователя с experiment_group в БД"):
            await self._create_user_and_lab("u1", experiment_group="group_a")
            assign_called = False

            def assign_forbidden():
                nonlocal assign_called
                assign_called = True
                return ExperimentGroup.GROUP_B

            monkeypatch.setattr(service, "assign_group", assign_forbidden)

        # Act
        with autotest.step("Создаём учебную сессию"):
            async with self.session_factory() as db:
                session = await service.create_session(db, "u1", "ospf-vlan-lab")

        # Assert
        with autotest.step("Проверяем сохранение группы"):
            user = await self._get_user("u1")
            assert_equal(user.experiment_group, "group_a", "experiment_group")
            assert_true(not assign_called, "assign_group не вызывается")

        with autotest.step("Проверяем сохранение учебной сессии"):
            saved_session = await self._get_learning_session(session.id)
            assert_equal(saved_session.user_id, "u1", "user_id")
            assert_equal(saved_session.lab_slug, "ospf-vlan-lab", "lab_slug")
            assert_equal(saved_session.status, "active", "status")
