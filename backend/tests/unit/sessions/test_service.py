import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from i18n import LocalizedError
from models.lab import Lab
from models.session import LearningSession
from models.user import User
from security.secrets import encrypt_secret
from sessions.services.launch import _create_provisioning_row, launch_session

pytestmark = [pytest.mark.unit]


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
            lab = Lab(slug=slug, title_i18n={"en": "Test Lab"}, enabled=enabled)
            db.add(lab)
            await db.commit()

    @autotest.num("1834")
    @autotest.external_id("ac2ec268-26a6-4412-ac47-1e84277ae5ba")
    @autotest.name("launch_session: disabled lab raises LocalizedError 'error.lab.disabled'")
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

        with autotest.step("Вызываем launch_session, ожидаем LocalizedError"):
            async with self.session_factory() as db:
                with pytest.raises(LocalizedError) as exc_info:
                    await launch_session(
                        db=db,
                        user_id="user-1",
                        lab_slug="test-lab",
                        gns3_client=None,
                        db_factory=self.session_factory,
                    )
                assert_equal(exc_info.value.key, "error.lab.disabled", "code=error.lab.disabled")


class TestCreateProvisioningRowPersistsLocale:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LearningSession.__table__.create)
        yield
        await self.engine.dispose()

    @autotest.num("3137")
    @autotest.external_id("91f96a50-0cb0-4bb5-adec-6768aa38960a")
    @autotest.name("launch: provisioning row persists the request locale onto the session")
    async def test_91f96a50_provisioning_row_persists_locale(self):
        with autotest.step("Act: create a provisioning row with locale=ru"):
            session = await _create_provisioning_row(
                self.session_factory, user_id="user-1", lab_slug="test-lab", locale="ru"
            )

        with autotest.step("Assert: session.locale persisted as ru"):
            assert_equal(session.locale, "ru", "session.locale persisted from launch")


class TestLaunchSessionRefreshesLocaleOnResume:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LearningSession.__table__.create)

        async with self.session_factory() as db:
            db.add(
                LearningSession(
                    id="s1",
                    user_id="user-1",
                    lab_slug="test-lab",
                    status="active",
                    locale="en",
                    meta={"gns3_username": "student", "enc_password": encrypt_secret("pw")},
                )
            )
            await db.commit()
        yield
        await self.engine.dispose()

    @autotest.num("3139")
    @autotest.external_id("bdaae934-c110-4fed-aed2-0990f3acf240")
    @autotest.name("launch: resuming an active session refreshes its stored locale on change")
    async def test_bdaae934_resume_refreshes_stored_locale(self):
        with autotest.step("Act: resume the active session requesting locale=ru"):
            async with self.session_factory() as db:
                await launch_session(
                    db=db,
                    user_id="user-1",
                    lab_slug="test-lab",
                    gns3_client=None,
                    db_factory=self.session_factory,
                    locale="ru",
                )
                await db.commit()

        with autotest.step("Assert: stored locale updated to ru on reread"):
            async with self.session_factory() as db:
                refetched = await db.get(LearningSession, "s1")
                assert_equal(refetched.locale, "ru", "stored locale refreshed on resume")
