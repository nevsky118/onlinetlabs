import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from control_interface.audit import record
from models.mcp_audit import MCPAudit

pytestmark = [pytest.mark.unit]


@pytest.fixture
async def audit_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(MCPAudit.__table__.create)
    async with session_factory() as db:
        yield db
    await engine.dispose()


class TestAudit:
    @autotest.num("1760")
    @autotest.external_id("f7a3e2b1-4c90-4d56-8e12-3a9f1b2c5d7e")
    @autotest.name("audit: act-вызов записан (источник воздействий)")
    async def test_f7a3e2b1_record_act(self, audit_db):
        with autotest.step("Act: записать act"):
            await record(audit_db, user_id="u1", session_id="s1", tool="execute_action",
                         kind="act", success=True, lab_slug="lan-static-ip")
        with autotest.step("Assert: строка есть, kind=act"):
            rows = (await audit_db.execute(select(MCPAudit))).scalars().all()
            assert_equal(len(rows), 1, "одна запись")
            assert_equal(rows[0].kind, "act", "kind")
