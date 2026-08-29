"""Verify SQLAlchemy constraints and default values on key tables."""

from datetime import datetime

import pytest
import pytest_asyncio
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.catalog import Course, Lab
from models.identity import Account, Session, User, UserRole
from models.learning import LearningSession

pytestmark = [pytest.mark.unit]


class TestModelConstraints:
    """Constraints, defaults, and cascading deletes."""

    @pytest_asyncio.fixture
    async def session(self):
        """In-memory SQLite + only the needed tables + PRAGMA foreign_keys=ON."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")

        @event.listens_for(engine.sync_engine, "connect")
        def _fk_on(dbapi_conn, value):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

        async with engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Account.__table__.create)
            await conn.run_sync(Session.__table__.create)
            await conn.run_sync(Course.__table__.create)
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LearningSession.__table__.create)

        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as async_session_2:
            yield async_session_2

        await engine.dispose()

    @autotest.num("750")
    @autotest.external_id("15fb7122-b250-4e00-b806-558c9290761f")
    @autotest.name("User.email UNIQUE: duplicate email raises IntegrityError")
    @pytest.mark.asyncio
    async def test_15fb7122_user_email_unique(self, session: AsyncSession):
        with autotest.step("Add the first user"):
            session.add(User(id="u1", email="dup@example.com"))
            await session.commit()

        with autotest.step("Inserting a second one with the same email must fail"):
            session.add(User(id="u2", email="dup@example.com"))
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

    @autotest.num("751")
    @autotest.external_id("4cad75ea-2c64-40d1-896c-a22e62fc8d55")
    @autotest.name("Account.user_id FK CASCADE: deleting a User deletes its Accounts")
    @pytest.mark.asyncio
    async def test_4cad75ea_account_cascade_on_user_delete(self, session: AsyncSession):
        with autotest.step("Create a User + two Accounts"):
            user = User(id="u-cascade", email="cascade@example.com")
            session.add(user)
            session.add(
                Account(
                    id="a1",
                    user_id="u-cascade",
                    type="oauth",
                    provider="github",
                    provider_account_id="gh-1",
                )
            )
            session.add(
                Account(
                    id="a2",
                    user_id="u-cascade",
                    type="oauth",
                    provider="google",
                    provider_account_id="g-1",
                )
            )
            await session.commit()

        with autotest.step("Delete the User"):
            await session.delete(user)
            await session.commit()

        with autotest.step("Accounts must be gone"):
            rows = (await session.execute(select(Account))).scalars().all()
            assert_equal(len(rows), 0, "no accounts after user delete")

    @autotest.num("752")
    @autotest.external_id("939fbc74-61db-45ec-b93c-3fb053c9c285")
    @autotest.name("User.role: default = 'student'")
    @pytest.mark.asyncio
    async def test_939fbc74_user_role_default_student(self, session: AsyncSession):
        with autotest.step("Create a User with no explicit role"):
            user = User(id="u-role", email="role@example.com")
            session.add(user)
            await session.commit()
            await session.refresh(user)

        with autotest.step("role must be 'student'"):
            assert_equal(user.role, "student", "role default")
            assert_equal(user.role, UserRole.STUDENT.value, "role == UserRole.STUDENT.value")

    @autotest.num("753")
    @autotest.external_id("a7a2ff3d-9868-4bc1-988b-076191fd4a59")
    @autotest.name("LearningSession.status default = 'active' and FK to user CASCADEs")
    @pytest.mark.asyncio
    async def test_a7a2ff3d_learning_session_defaults_and_cascade(self, session: AsyncSession):
        with autotest.step("Create a User and a Lab"):
            user = User(id="u-ls", email="ls@example.com")
            lab = Lab(slug="lab-1", title_i18n={"en": "Lab 1"})
            session.add(user)
            session.add(lab)
            await session.commit()

        with autotest.step("Create a LearningSession with no explicit status/started_at"):
            ls = LearningSession(user_id="u-ls", lab_slug="lab-1")
            session.add(ls)
            await session.commit()
            await session.refresh(ls)

        with autotest.step("status='active', started_at set, ended_at=None"):
            assert_equal(ls.status, "active", "status default")
            assert_true(isinstance(ls.started_at, datetime), "started_at is datetime")
            assert_is_none(ls.ended_at, "ended_at is None")

        with autotest.step("Delete the User, the LearningSession must be gone"):
            await session.delete(user)
            await session.commit()
            rows = (await session.execute(select(LearningSession))).scalars().all()
            assert_equal(len(rows), 0, "no learning_sessions after user delete")

    @autotest.num("754")
    @autotest.external_id("b774dcda-915e-4548-b743-b1a822a85fce")
    @autotest.name("User.id auto-generates a UUID when no explicit value is given")
    @pytest.mark.asyncio
    async def test_b774dcda_user_id_auto_uuid(self, session: AsyncSession):
        with autotest.step("Create a User with no id"):
            user = User(email="autoid@example.com")
            session.add(user)
            await session.commit()
            await session.refresh(user)

        with autotest.step("id is set and looks like a UUID"):
            assert_true(user.id is not None, "id is set")
            assert_equal(len(user.id), 36, "uuid length 36")
            assert_equal(user.id.count("-"), 4, "uuid has 4 dashes")

    @autotest.num("755")
    @autotest.external_id("88ae0d4c-9d98-4612-9038-9239a409cfb8")
    @autotest.name("Account.id auto-generates a UUID when no explicit value is given")
    @pytest.mark.asyncio
    async def test_88ae0d4c_account_id_auto_uuid(self, session: AsyncSession):
        with autotest.step("Create a User + Account with no id"):
            session.add(User(id="u-acc-uuid", email="acc-uuid@example.com"))
            await session.commit()

            acc = Account(
                user_id="u-acc-uuid",
                type="oauth",
                provider="github",
                provider_account_id="gh-x",
            )
            session.add(acc)
            await session.commit()
            await session.refresh(acc)

        with autotest.step("id is set and looks like a UUID"):
            assert_true(acc.id is not None, "id is set")
            assert_equal(len(acc.id), 36, "uuid length 36")
            assert_equal(acc.id.count("-"), 4, "uuid has 4 dashes")

    @autotest.num("756")
    @autotest.external_id("9e0ad8de-e339-4621-8278-4b8b49f398e4")
    @autotest.name("Account with a nonexistent user_id raises IntegrityError (FK enforced)")
    @pytest.mark.asyncio
    async def test_9e0ad8de_account_fk_enforced(self, session: AsyncSession):
        with autotest.step("Account referencing a nonexistent user"):
            session.add(
                Account(
                    id="orphan",
                    user_id="missing",
                    type="oauth",
                    provider="github",
                    provider_account_id="gh-missing",
                )
            )
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()
