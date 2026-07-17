"""no_assist in session state: L2 holdout (proactive suppressed) is visible to the front end as noAssist."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.lab import Lab
from models.progress import LabProgress
from models.session import LearningSession
from models.user import User
from sessions.schemas import FullSessionStateResponse
from sessions.services.query import get_session_state

pytestmark = [pytest.mark.unit]

_SKILL = "static-ip-addressing"


class _Cache:
    async def get(self, sid):
        return None

    async def set(self, sid, val):
        return None


@pytest.fixture
async def db_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sf = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Lab.__table__.create)
        await conn.run_sync(LabProgress.__table__.create)
        await conn.run_sync(LearningSession.__table__.create)
    now = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
    async with sf() as db:
        db.add(User(id="u1", email="u1@test.local", control_arm="closed"))
        db.add(User(id="u2", email="u2@test.local", control_arm="closed"))
        db.add(Lab(slug="l1", title="L1", meta={"skill": _SKILL}))
        db.add(Lab(slug="l2", title="L2", meta={"skill": _SKILL}))
        db.add(LabProgress(id="p1", user_id="u1", lab_slug="l1", status="completed"))
        # u1 on l2 = L2 holdout (has a completed l1 of the same skill)
        db.add(
            LearningSession(
                id="sess-u1",
                user_id="u1",
                lab_slug="l2",
                status="active",
                started_at=now,
                meta={"gns3_service_session_id": "gsid"},
            )
        )
        # u2 on l2 = not L2 (no completed labs)
        db.add(
            LearningSession(
                id="sess-u2",
                user_id="u2",
                lab_slug="l2",
                status="active",
                started_at=now,
                meta={"gns3_service_session_id": "gsid"},
            )
        )
        await db.commit()
    yield sf
    await engine.dispose()


def _gns3():
    client = AsyncMock()
    client.get_state = AsyncMock(return_value={"nodes": [], "links": [], "metrics": {}})
    return client


class TestSessionStateNoAssist:
    @autotest.num("2007")
    @autotest.external_id("91794f12-2555-4624-ab08-9d8a074191b5")
    @autotest.name("Schema: no_assist сериализуется как noAssist (by-alias), дефолт False")
    def test_91794f12_schema_alias_and_default(self):
        with autotest.step("Assert: поле есть, alias noAssist, дефолт False"):
            field = FullSessionStateResponse.model_fields["no_assist"]
            assert_equal(field.alias, "noAssist", "alias == noAssist")
            assert_equal(field.default, False, "дефолт False")

    @autotest.num("2008")
    @autotest.external_id("d60f1ae3-c868-406b-a0d5-189a9af55a57")
    @autotest.name("get_session_state: no_assist=True на L2-холдауте")
    async def test_d60f1ae3_no_assist_true_on_l2(self, db_factory):
        with autotest.step("Act: состояние сессии u1 на l2 (есть завершённая l1)"):
            async with db_factory() as db:
                state = await get_session_state(db, "sess-u1", "u1", _gns3(), _Cache())

        with autotest.step("Assert: no_assist == True"):
            assert_true(state is not None, "состояние получено")
            assert_equal(state["no_assist"], True, "L2-холдаут → no_assist True")

    @autotest.num("2009")
    @autotest.external_id("4ba89ec7-f060-4a43-8e77-a4d19df92f6b")
    @autotest.name("get_session_state: no_assist=False без предшествующей лабы навыка")
    async def test_4ba89ec7_no_assist_false_otherwise(self, db_factory):
        with autotest.step("Act: состояние сессии u2 на l2 (нет завершённых лаб)"):
            async with db_factory() as db:
                state = await get_session_state(db, "sess-u2", "u2", _gns3(), _Cache())

        with autotest.step("Assert: no_assist == False"):
            assert_equal(state["no_assist"], False, "не L2 → no_assist False")
