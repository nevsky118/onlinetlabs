import pytest
from mcp_sdk.testing import autotest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.lab import Lab
from models.user import User
from sessions.services.launch import launch_session

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

        with autotest.step("Вызываем launch_session, ожидаем ValueError"):
            async with self.session_factory() as db:
                with pytest.raises(ValueError, match="Лаба отключена"):
                    await launch_session(
                        db=db,
                        user_id="user-1",
                        lab_slug="test-lab",
                        gns3_client=None,
                        db_factory=self.session_factory,
                    )
