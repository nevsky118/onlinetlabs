import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_false, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from control_interface.consent import grant, has_consent, revoke
from control_interface.registry import ToolKind
from models.consent import Consent

pytestmark = [pytest.mark.unit]


@pytest.fixture
async def consent_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Consent.__table__.create)
    async with session_factory() as db:
        yield db
    await engine.dispose()


class TestConsentService:
    @autotest.num("1750")
    @autotest.external_id("a3f2c1d4-7e89-4b56-9c01-2d3e4f5a6b7c")
    @autotest.name("consent: study покрывает observe и act")
    async def test_a3f2c1d4_study_covers_all(self, consent_db):
        with autotest.step("Arrange: study-согласие"):
            await grant(consent_db, "u1", "study", observe=True, act=True)
        with autotest.step("Assert: и observe, и act разрешены"):
            assert_true(await has_consent(consent_db, "u1", ToolKind.OBSERVE), "observe")
            assert_true(await has_consent(consent_db, "u1", ToolKind.ACT), "act")

    @autotest.num("1751")
    @autotest.external_id("6aa6be22-d787-4a58-8dab-859e0cd22ab4")
    @autotest.name("consent: product гранулярно (observe да, act нет)")
    async def test_6aa6be22_product_granular(self, consent_db):
        with autotest.step("Arrange: product observe=True act=False"):
            await grant(consent_db, "u2", "product", observe=True, act=False)
        with autotest.step("Assert: observe разрешён, act нет"):
            assert_true(await has_consent(consent_db, "u2", ToolKind.OBSERVE), "observe")
            assert_false(await has_consent(consent_db, "u2", ToolKind.ACT), "act-нет")

    @autotest.num("1752")
    @autotest.external_id("bf9e3fd5-7f19-4732-b87d-ec19e0c264b1")
    @autotest.name("consent: отзыв прекращает согласие")
    async def test_bf9e3fd5_revoke(self, consent_db):
        with autotest.step("Arrange+Act: дать study, затем отозвать"):
            await grant(consent_db, "u3", "study", observe=True, act=True)
            n = await revoke(consent_db, "u3", "study")
        with autotest.step("Assert: отозвано 1, согласия нет"):
            assert_equal(n, 1, "отозвано")
            assert_false(await has_consent(consent_db, "u3", ToolKind.OBSERVE), "нет после отзыва")
