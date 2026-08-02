"""Tests for the handler logic of consent and audit-query endpoints, without spinning up FastAPI."""

from datetime import UTC

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from control_interface.consent import grant, revoke
from control_interface.schemas import ConsentGrantRequest, ConsentResponse, ConsentRevokeResponse
from instructor.schemas import MCPAuditRow
from models.consent import Consent
from models.mcp_audit import MCPAudit

pytestmark = [pytest.mark.unit]


@pytest.fixture
async def endpoint_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Consent.__table__.create)
        await conn.run_sync(MCPAudit.__table__.create)
    async with session_factory() as db:
        yield db
    await engine.dispose()


class TestConsentEndpointLogic:
    @autotest.num("1780")
    @autotest.external_id("0838160b-40df-437c-8531-f46d16f52ab8")
    @autotest.name("consent POST: grant returns Consent, fields correct")
    async def test_0838160b_grant_returns_consent(self, endpoint_db):
        with autotest.step("Arrange: study consent request"):
            req = ConsentGrantRequest(scope="study", observe=True, act=True)
        with autotest.step("Act: call grant handler logic"):
            c = await grant(
                endpoint_db,
                "user-11111111-0000-0000-0000-000000000001",
                req.scope,
                req.observe,
                req.act,
                req.data_policy,
            )
        with autotest.step("Assert: scope, observe, act set; revoked_at None"):
            resp = ConsentResponse.model_validate(c)
            assert_equal(resp.scope, "study", "scope")
            assert_equal(resp.observe, True, "observe")
            assert_equal(resp.act, True, "act")
            assert_is_none(resp.revoked_at, "not revoked")

    @autotest.num("1781")
    @autotest.external_id("a2b3c4d5-e6f7-4a89-0123-4b5c6d7e8f90")
    @autotest.name("consent POST: product observe=True act=False, schema correct")
    async def test_a2b3c4d5_grant_product_granular(self, endpoint_db):
        with autotest.step("Act: product with restricted act"):
            c = await grant(
                endpoint_db,
                "user-22222222-0000-0000-0000-000000000002",
                "product",
                observe=True,
                act=False,
            )
        with autotest.step("Assert: act=False in schema"):
            resp = ConsentResponse.model_validate(c)
            assert_equal(resp.scope, "product", "scope")
            assert_equal(resp.act, False, "act=False")

    @autotest.num("1782")
    @autotest.external_id("b3c4d5e6-f7a8-4b90-1234-5c6d7e8f9012")
    @autotest.name("consent DELETE: revoke returns count, schema ConsentRevokeResponse")
    async def test_b3c4d5e6_revoke_count(self, endpoint_db):
        with autotest.step("Arrange: grant study consent"):
            await grant(
                endpoint_db,
                "user-33333333-0000-0000-0000-000000000003",
                "study",
                observe=True,
                act=True,
            )
        with autotest.step("Act: revoke it"):
            n = await revoke(endpoint_db, "user-33333333-0000-0000-0000-000000000003", "study")
        with autotest.step("Assert: 1 revoked, schema valid"):
            resp = ConsentRevokeResponse(revoked=n)
            assert_equal(resp.revoked, 1, "count=1")

    @autotest.num("1783")
    @autotest.external_id("c4d5e6f7-a8b9-4c01-2345-6d7e8f901234")
    @autotest.name("audit GET: MCPAuditRow schema builds from an MCPAudit row")
    async def test_c4d5e6f7_audit_row_schema(self, endpoint_db):
        with autotest.step("Arrange: insert an audit row manually"):
            from datetime import datetime
            from uuid import uuid4

            row = MCPAudit(
                id=str(uuid4()),
                user_id="user-44444444-0000-0000-0000-000000000004",
                session_id="sess-55555555-0000-0000-0000-000000000005",
                tool="list_user_actions",
                kind="observe",
                ts=datetime.now(UTC),
                success=True,
            )
            endpoint_db.add(row)
            await endpoint_db.commit()
        with autotest.step("Assert: schema builds without errors, kind=observe"):
            fetched = (await endpoint_db.execute(select(MCPAudit))).scalars().first()
            schema = MCPAuditRow.model_validate(fetched)
            assert_equal(schema.kind, "observe", "kind")
            assert_equal(schema.tool, "list_user_actions", "tool")

    @autotest.num("1784")
    @autotest.external_id("d5e6f7a8-b9c0-4d12-3456-7e8f90123456")
    @autotest.name("audit GET: filtering by kind=act returns only act rows")
    async def test_d5e6f7a8_audit_filter_kind(self, endpoint_db):
        with autotest.step("Arrange: two audit calls, observe and act"):
            from datetime import datetime
            from uuid import uuid4

            for kind in ("observe", "act"):
                endpoint_db.add(
                    MCPAudit(
                        id=str(uuid4()),
                        user_id="user-66666666-0000-0000-0000-000000000006",
                        session_id="sess-77777777-0000-0000-0000-000000000007",
                        tool="execute_action" if kind == "act" else "get_logs",
                        kind=kind,
                        ts=datetime.now(UTC),
                        success=True,
                    )
                )
            await endpoint_db.commit()
        with autotest.step("Act: query filtered by kind=act"):
            rows = (
                (await endpoint_db.execute(select(MCPAudit).where(MCPAudit.kind == "act")))
                .scalars()
                .all()
            )
        with autotest.step("Assert: only act rows"):
            schemas = [MCPAuditRow.model_validate(r) for r in rows]
            assert_equal(len(schemas), 1, "one row")
            assert_equal(schemas[0].kind, "act", "kind=act")
