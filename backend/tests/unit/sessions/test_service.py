import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from i18n import LocalizedError
from kit.secrets import encrypt_secret
from models.catalog import Lab
from models.identity import User
from models.learning import LearningSession
from sessions.services.launch import _create_provisioning_row, launch_session
from sessions.services.ticket import TicketStore
from tests.settings.data.queue_data import TicketRedisData
from tests.settings.data.sessions_data import ProvisioningGns3Data

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
        with autotest.step("Arrange: import launch_mod"):
            import sessions.services.launch as launch_mod

        with autotest.step("Create a disabled lab"):
            await self._insert_lab("test-lab", enabled=False)

        with autotest.step("Patch get_active_session and count_active_sessions"):

            async def _no_session(*a, **kw):
                return None

            async def _zero_count(*a, **kw):
                return 0

            monkeypatch.setattr(launch_mod, "get_active_session", _no_session)
            monkeypatch.setattr(launch_mod, "count_active_sessions", _zero_count)

        with autotest.step("Call launch_session, expect LocalizedError"):
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
                    ticket_store=TicketStore(redis=TicketRedisData()),
                )
                await db.commit()

        with autotest.step("Assert: stored locale updated to ru on reread"):
            async with self.session_factory() as db:
                refetched = await db.get(LearningSession, "s1")
                assert_equal(refetched.locale, "ru", "stored locale refreshed on resume")


class TestLaunchSessionStartsNodes:
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
                Lab(
                    slug="test-lab",
                    title_i18n={"en": "Test Lab"},
                    enabled=True,
                    gns3_template_project_id="tpl-1",
                )
            )
            await db.commit()
        yield
        await self.engine.dispose()

    async def _launch(self, gns3):
        async with self.session_factory() as db:
            return await launch_session(
                db=db,
                user_id="user-1",
                lab_slug="test-lab",
                gns3_client=gns3,
                db_factory=self.session_factory,
                ticket_store=TicketStore(redis=TicketRedisData()),
            )

    @autotest.num("3500")
    @autotest.external_id("4045540c-854b-467f-b66b-3cb4d829dcf4")
    @autotest.name("launch: a freshly provisioned session starts its nodes")
    async def test_4045540c_provisioning_starts_the_nodes(self):
        with autotest.step("Arrange: a gns3 client that records bulk actions"):
            gns3 = ProvisioningGns3Data()

        with autotest.step("Act: launch the lab"):
            await self._launch(gns3)

        with autotest.step("Assert: the nodes were asked to start"):
            assert_equal(gns3.bulk_actions, [("gns3-sid-1", "start")], "start requested once")

    @autotest.num("3501")
    @autotest.external_id("6da72e8d-b65d-4c21-9315-a2dd9af97955")
    @autotest.name("launch: a refused start does not fail the launch")
    async def test_6da72e8d_failed_start_keeps_the_session(self):
        with autotest.step("Arrange: a gns3 client whose bulk action fails"):
            gns3 = ProvisioningGns3Data(fail_bulk=True)

        with autotest.step("Act: launch the lab"):
            session, creds = await self._launch(gns3)

        with autotest.step("Assert: the session is still handed to the student"):
            assert_equal(session.status, "active", "session active")
            assert_equal(creds["gns3_username"], "student-1", "credentials returned")
