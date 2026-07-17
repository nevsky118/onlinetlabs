"""Tests for GET/DELETE /users/me/sessions."""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from auth.dependencies import get_current_user
from db.session import get_db
from models.user import Session, User
from users.router import router as users_router

pytestmark = [pytest.mark.unit]

_USER_A = {"id": "user-a", "role": "student"}
_USER_B = {"id": "user-b", "role": "student"}


def _make_session(session_id: str, user_id: str, offset_days: int = 0) -> Session:
    from datetime import timedelta

    return Session(
        id=session_id,
        session_token=str(uuid.uuid4()),
        user_id=user_id,
        expires=datetime(2030, 1, 1, tzinfo=UTC) + timedelta(days=offset_days),
    )


class TestSessionEndpoints:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Session.__table__.create)

        async with self.session_factory() as db:
            db.add_all(
                [
                    User(id="user-a", name="Alice", email="alice@test.local", role="student"),
                    User(id="user-b", name="Bob", email="bob@test.local", role="student"),
                ]
            )
            await db.commit()

        self.app = self._build_app(_USER_A)
        self.app_b = self._build_app(_USER_B)

        yield
        await self.engine.dispose()

    def _build_app(self, user: dict) -> FastAPI:
        app = FastAPI()
        app.include_router(users_router, prefix="/users/me")

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_current_user] = lambda: user
        return app

    def _client(self, app: FastAPI | None = None) -> AsyncClient:
        return AsyncClient(
            transport=ASGITransport(app=app or self.app),
            base_url="http://testserver",
        )

    async def _seed(self, *sessions: Session) -> None:
        async with self.session_factory() as db:
            db.add_all(sessions)
            await db.commit()

    @autotest.num("1945")
    @autotest.external_id("f4ab80d0-6b59-4a5e-b047-0ad2383af47a")
    @autotest.name("GET /sessions: возвращает сессии пользователя и count")
    async def test_f4ab80d0_list_returns_sessions_and_count(self):
        s1 = _make_session("s1", "user-a", offset_days=1)
        s2 = _make_session("s2", "user-a", offset_days=0)
        s3 = _make_session("s3", "user-b")  # belongs to someone else
        await self._seed(s1, s2, s3)

        with autotest.step("Act: GET /users/me/sessions от user-a"):
            async with self._client() as client:
                resp = await client.get("/users/me/sessions")

        with autotest.step("Assert: 200, count=2, только сессии user-a"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_equal(body["count"], 2, "count=2")
            assert_equal(len(body["sessions"]), 2, "sessions len=2")
            ids = {s["id"] for s in body["sessions"]}
            assert_true("s1" in ids and "s2" in ids, "только s1 и s2")
            assert_true("s3" not in ids, "s3 чужая — не возвращается")

    @autotest.num("1946")
    @autotest.external_id("696f19c2-bab1-43a8-9b55-b99373e9e55e")
    @autotest.name("DELETE /sessions/{id}: удаляет одну сессию пользователя")
    async def test_696f19c2_delete_single_session(self):
        s1 = _make_session("s1", "user-a")
        s2 = _make_session("s2", "user-a")
        await self._seed(s1, s2)

        with autotest.step("Act: DELETE /users/me/sessions/s1"):
            async with self._client() as client:
                resp = await client.delete("/users/me/sessions/s1")

        with autotest.step("Assert: 200, revoked=1"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_equal(resp.json()["revoked"], 1, "revoked=1")

        with autotest.step("Assert: GET возвращает только s2"):
            async with self._client() as client:
                list_resp = await client.get("/users/me/sessions")
            assert_equal(list_resp.json()["count"], 1, "осталась 1 сессия")
            assert_equal(list_resp.json()["sessions"][0]["id"], "s2", "id=s2")

    @autotest.num("1947")
    @autotest.external_id("94daf388-acc2-4682-a4c1-889d1d0e4405")
    @autotest.name("DELETE /sessions/{id}: чужая/несуществующая → 404")
    async def test_94daf388_delete_foreign_or_missing_404(self):
        s_b = _make_session("sb1", "user-b")
        await self._seed(s_b)

        with autotest.step("Act: user-a удаляет чужую сессию sb1"):
            async with self._client() as client:
                resp_foreign = await client.delete("/users/me/sessions/sb1")

        with autotest.step("Assert: 404 для чужой сессии"):
            assert_equal(resp_foreign.status_code, 404, "чужая → 404")

        with autotest.step("Act: user-a удаляет несуществующую сессию"):
            async with self._client() as client:
                resp_missing = await client.delete("/users/me/sessions/does-not-exist")

        with autotest.step("Assert: 404 для несуществующей"):
            assert_equal(resp_missing.status_code, 404, "несуществующая → 404")

    @autotest.num("1948")
    @autotest.external_id("e838e96a-6c34-4cdd-809b-7ad70c67904f")
    @autotest.name("DELETE /sessions: удаляет все сессии, revoked==2, GET возвращает count=0")
    async def test_e838e96a_delete_all_sessions(self):
        s1 = _make_session("sa1", "user-a")
        s2 = _make_session("sa2", "user-a")
        await self._seed(s1, s2)

        with autotest.step("Act: DELETE /users/me/sessions (all)"):
            async with self._client() as client:
                resp = await client.delete("/users/me/sessions")

        with autotest.step("Assert: revoked=2"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_equal(resp.json()["revoked"], 2, "revoked=2")

        with autotest.step("Assert: GET возвращает count=0"):
            async with self._client() as client:
                list_resp = await client.get("/users/me/sessions")
            assert_equal(list_resp.json()["count"], 0, "count=0 после удаления всех")
