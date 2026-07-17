"""PATCH /sessions/{id}: encrypted credentials (session.meta) must not leak into the response."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from auth.dependencies import get_current_user
from db.session import get_db
from models.behavioral_event import BehavioralEvent
from models.experiment import ExperimentMetrics
from models.lab import Lab, LabStep
from models.progress import LabProgress
from models.session import LearningSession
from models.user import User
from sessions.routers.commands import router as commands_router

pytestmark = [pytest.mark.unit]

_USER_ID = "user-meta-1"
_SESSION_ID = "sess-meta-1"
_SECRET_META = {
    "gns3_service_session_id": "gsess-1",
    "gns3_user_id": "gu-1",
    "gns3_username": "student",
    "gns3_project_id": "proj-1",
    "enc_password": "enc:sekret-password",
    "enc_jwt": "enc:sekret-jwt",
}


class TestLifecycleMetaLeak:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            # disable FK in SQLite, tables are created independently
            await conn.execute(text("PRAGMA foreign_keys = OFF"))
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LabStep.__table__.create)
            await conn.run_sync(LearningSession.__table__.create)
            await conn.run_sync(LabProgress.__table__.create)
            await conn.run_sync(BehavioralEvent.__table__.create)
            await conn.run_sync(ExperimentMetrics.__table__.create)

        async with self.session_factory() as db:
            db.add(
                User(
                    id=_USER_ID,
                    email="meta-leak@test.local",
                    control_arm="closed",
                    experiment_group="group_b",
                )
            )
            db.add(Lab(slug="lab-meta", title="Lab Meta"))
            db.add(
                LearningSession(
                    id=_SESSION_ID,
                    user_id=_USER_ID,
                    lab_slug="lab-meta",
                    status="active",
                    started_at=datetime.now(UTC) - timedelta(minutes=5),
                    meta=dict(_SECRET_META),
                )
            )
            await db.commit()

        app = FastAPI()
        app.include_router(commands_router, prefix="/sessions")

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_current_user] = lambda: {"id": _USER_ID, "role": "student"}
        self.app = app

        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    @autotest.num("2400")
    @autotest.external_id("3557155f-c03b-4664-94ea-f603593f50da")
    @autotest.name("PATCH /sessions/{id}: не отдаёт зашифрованные креды в meta ответа")
    async def test_3557155f_patch_response_meta_is_none(self):
        with autotest.step("Act: PATCH /sessions/{id} со статусом ended"):
            async with self._client() as client:
                resp = await client.patch(f"/sessions/{_SESSION_ID}", json={"status": "ended"})

        with autotest.step("Assert: 200, статус обновлён, meta не утекла клиенту"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_equal(body["status"], "ended", "статус обновлён")
            assert_is_none(body["meta"], "meta не отдаётся клиенту (зашифрованные креды)")
