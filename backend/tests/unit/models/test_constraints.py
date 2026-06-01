"""Проверка SQLAlchemy constraints и значений по умолчанию на ключевых таблицах."""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true

from models.course import Course
from models.lab import Lab
from models.session import LearningSession
from models.user import Account, Session, User, UserRole

pytestmark = [pytest.mark.unit]


class TestModelConstraints:
    """Constraints, дефолты и каскадные удаления."""

    @pytest_asyncio.fixture
    async def session(self):
        """In-memory SQLite + только нужные таблицы + PRAGMA foreign_keys=ON."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")

        @event.listens_for(engine.sync_engine, "connect")
        def _fk_on(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

        async with engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Account.__table__.create)
            await conn.run_sync(Session.__table__.create)
            await conn.run_sync(Course.__table__.create)
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LearningSession.__table__.create)

        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as s:
            yield s

        await engine.dispose()

    @autotest.num("750")
    @autotest.external_id("c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f")
    @autotest.name("User.email UNIQUE: дубликат email вызывает IntegrityError")
    @pytest.mark.asyncio
    async def test_c1d2e3f4_user_email_unique(self, session: AsyncSession):
        with autotest.step("Добавляем первого пользователя"):
            session.add(User(id="u1", email="dup@example.com"))
            await session.commit()

        with autotest.step("Вставка второго с тем же email должна упасть"):
            session.add(User(id="u2", email="dup@example.com"))
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

    @autotest.num("751")
    @autotest.external_id("d2e3f4a5-b6c7-4d8e-9f0a-1b2c3d4e5f60")
    @autotest.name("Account.user_id FK CASCADE: удаление User удаляет его Account-ы")
    @pytest.mark.asyncio
    async def test_d2e3f4a5_account_cascade_on_user_delete(self, session: AsyncSession):
        with autotest.step("Создаём User + два Account"):
            user = User(id="u-cascade", email="cascade@example.com")
            session.add(user)
            session.add(Account(
                id="a1", user_id="u-cascade", type="oauth",
                provider="github", provider_account_id="gh-1",
            ))
            session.add(Account(
                id="a2", user_id="u-cascade", type="oauth",
                provider="google", provider_account_id="g-1",
            ))
            await session.commit()

        with autotest.step("Удаляем User"):
            await session.delete(user)
            await session.commit()

        with autotest.step("Account-ы должны исчезнуть"):
            rows = (await session.execute(select(Account))).scalars().all()
            assert_equal(len(rows), 0, "no accounts after user delete")

    @autotest.num("752")
    @autotest.external_id("e3f4a5b6-c7d8-4e9f-a0b1-2c3d4e5f6071")
    @autotest.name("User.role: дефолт = 'student'")
    @pytest.mark.asyncio
    async def test_e3f4a5b6_user_role_default_student(self, session: AsyncSession):
        with autotest.step("Создаём User без явной роли"):
            user = User(id="u-role", email="role@example.com")
            session.add(user)
            await session.commit()
            await session.refresh(user)

        with autotest.step("role должна быть 'student'"):
            assert_equal(user.role, "student", "role default")
            assert_equal(user.role, UserRole.STUDENT.value, "role == UserRole.STUDENT.value")

    @autotest.num("753")
    @autotest.external_id("f4a5b6c7-d8e9-4f0a-b1c2-3d4e5f607182")
    @autotest.name("LearningSession.status дефолт = 'active' и FK к user работает CASCADE")
    @pytest.mark.asyncio
    async def test_f4a5b6c7_learning_session_defaults_and_cascade(self, session: AsyncSession):
        with autotest.step("Создаём User и Lab"):
            user = User(id="u-ls", email="ls@example.com")
            lab = Lab(slug="lab-1", title="Lab 1")
            session.add(user)
            session.add(lab)
            await session.commit()

        with autotest.step("Создаём LearningSession без явного status/started_at"):
            ls = LearningSession(user_id="u-ls", lab_slug="lab-1")
            session.add(ls)
            await session.commit()
            await session.refresh(ls)

        with autotest.step("status='active', started_at заполнен, ended_at=None"):
            assert_equal(ls.status, "active", "status default")
            assert_true(isinstance(ls.started_at, datetime), "started_at is datetime")
            assert_is_none(ls.ended_at, "ended_at is None")

        with autotest.step("Удаляем User — LearningSession должен исчезнуть"):
            await session.delete(user)
            await session.commit()
            rows = (await session.execute(select(LearningSession))).scalars().all()
            assert_equal(len(rows), 0, "no learning_sessions after user delete")

    @autotest.num("754")
    @autotest.external_id("a5b6c7d8-e9f0-4a1b-c2d3-4e5f60718293")
    @autotest.name("User.id auto-генерируется UUID при отсутствии явного значения")
    @pytest.mark.asyncio
    async def test_a5b6c7d8_user_id_auto_uuid(self, session: AsyncSession):
        with autotest.step("Создаём User без id"):
            user = User(email="autoid@example.com")
            session.add(user)
            await session.commit()
            await session.refresh(user)

        with autotest.step("id заполнен и похож на UUID"):
            assert_true(user.id is not None, "id is set")
            assert_equal(len(user.id), 36, "uuid length 36")
            assert_equal(user.id.count("-"), 4, "uuid has 4 dashes")

    @autotest.num("755")
    @autotest.external_id("b6c7d8e9-f0a1-4b2c-d3e4-5f6071829304")
    @autotest.name("Account.id auto-генерируется UUID при отсутствии явного значения")
    @pytest.mark.asyncio
    async def test_b6c7d8e9_account_id_auto_uuid(self, session: AsyncSession):
        with autotest.step("Создаём User + Account без id"):
            session.add(User(id="u-acc-uuid", email="acc-uuid@example.com"))
            await session.commit()

            acc = Account(
                user_id="u-acc-uuid", type="oauth",
                provider="github", provider_account_id="gh-x",
            )
            session.add(acc)
            await session.commit()
            await session.refresh(acc)

        with autotest.step("id заполнен и похож на UUID"):
            assert_true(acc.id is not None, "id is set")
            assert_equal(len(acc.id), 36, "uuid length 36")
            assert_equal(acc.id.count("-"), 4, "uuid has 4 dashes")

    @autotest.num("756")
    @autotest.external_id("c7d8e9f0-a1b2-4c3d-e4f5-607182930415")
    @autotest.name("Account без существующего user_id вызывает IntegrityError (FK enforced)")
    @pytest.mark.asyncio
    async def test_c7d8e9f0_account_fk_enforced(self, session: AsyncSession):
        with autotest.step("Account, ссылающийся на несуществующего user"):
            session.add(Account(
                id="orphan", user_id="missing", type="oauth",
                provider="github", provider_account_id="gh-missing",
            ))
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()
