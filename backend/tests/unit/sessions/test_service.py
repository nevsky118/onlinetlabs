import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from experiment.assignment import ExperimentGroup
from models.lab import Lab
from models.user import User
from sessions.services.launch import assign_experiment_group_if_needed, launch_session

pytestmark = [pytest.mark.unit]


class TestAssignExperimentGroupIfNeeded:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        # Create only the tables the test needs. Full metadata has
        # JSONB columns with server_default '::jsonb', which SQLite doesn't understand.
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Lab.__table__.create)
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

    @autotest.num("650")
    @autotest.external_id("7bc8fd0e-1aa4-4f46-a443-bcf1928a2ca8")
    @autotest.name("assign_experiment_group_if_needed: новый user получает группу из DI")
    async def test_7bc8fd0e_assigns_group_via_di(self):
        # Arrange
        with autotest.step("Готовим пользователя без experiment_group"):
            await self._create_user_and_lab("u1", experiment_group=None)

        # Act
        with autotest.step("Вызываем с фейк-assigner через DI"):
            async with self.session_factory() as db:
                await assign_experiment_group_if_needed(
                    db,
                    "u1",
                    group_assigner=lambda: ExperimentGroup.GROUP_B,
                )
                await db.commit()

        # Assert
        with autotest.step("Группа из DI сохранена в БД"):
            user = await self._get_user("u1")
            assert_equal(user.experiment_group, "group_b", "experiment_group")

    @autotest.num("651")
    @autotest.external_id("a0d67028-622f-48b0-8380-73e4c86b06fb")
    @autotest.name("assign_experiment_group_if_needed: существующая группа не перезаписывается")
    async def test_a0d67028_keeps_existing_group(self):
        # Arrange
        with autotest.step("Готовим пользователя с experiment_group=group_a"):
            await self._create_user_and_lab("u1", experiment_group="group_a")

        # Act
        with autotest.step("Вызываем с фейк-assigner и считаем вызовы"):
            assign_called = False

            def assign_forbidden() -> ExperimentGroup:
                nonlocal assign_called
                assign_called = True
                return ExperimentGroup.GROUP_B

            async with self.session_factory() as db:
                await assign_experiment_group_if_needed(
                    db,
                    "u1",
                    group_assigner=assign_forbidden,
                )
                await db.commit()

        # Assert
        with autotest.step("Группа не меняется и assigner не вызван"):
            user = await self._get_user("u1")
            assert_equal(user.experiment_group, "group_a", "experiment_group")
            assert not assign_called, "assigner не должен вызываться"


class TestLaunchSessionDisabledLab:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Lab.__table__.create)
        yield
        await self.engine.dispose()

    async def _insert_lab(self, slug: str, enabled: bool) -> None:
        async with self.session_factory() as db:
            lab = Lab(slug=slug, title="Test Lab", enabled=enabled)
            db.add(lab)
            await db.commit()

    @autotest.num("1834")
    @autotest.external_id("ac2ec268-26a6-4412-ac47-1e84277ae5ba")
    @autotest.name("launch_session: disabled lab raises ValueError 'Лаба отключена'")
    async def test_ac2ec268_disabled_lab_raises(self, monkeypatch):
        import sessions.services.launch as launch_mod

        with autotest.step("Создаём отключённую лабу"):
            await self._insert_lab("test-lab", enabled=False)

        async def _no_session(*a, **kw):
            return None

        async def _zero_count(*a, **kw):
            return 0

        with autotest.step("Патчим get_active_session и count_active_sessions"):
            monkeypatch.setattr(launch_mod, "get_active_session", _no_session)
            monkeypatch.setattr(launch_mod, "count_active_sessions", _zero_count)

        with autotest.step("Вызываем launch_session — ожидаем ValueError"):
            async with self.session_factory() as db:
                with pytest.raises(ValueError, match="Лаба отключена"):
                    await launch_session(
                        db=db,
                        user_id="user-1",
                        lab_slug="test-lab",
                        gns3_client=None,
                        db_factory=self.session_factory,
                    )
