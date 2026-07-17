"""Account activation gate tests: require_active_user, JWT round-trip, admin PATCH, /auth/activate."""

import uuid

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from admin.router import router as admin_router
from auth.dependencies import (
    create_backend_token,
    get_current_user,
    require_active_user,
)
from auth.router import router as auth_router
from auth.service import create_user, upsert_github_user
from config import settings
from db.session import get_db
from models.user import Account, User
from rate_limit import limiter

pytestmark = [pytest.mark.unit]

_ADMIN_USER = {"id": "admin-001", "role": "admin", "is_active": True}


class TestRequireActiveUser:
    @autotest.num("1956")
    @autotest.external_id("ed94fd09-5b5f-4345-b41f-5364f08d945c")
    @autotest.name("require_active_user: активный пользователь проходит")
    def test_ed94fd09_active_passes(self):
        with autotest.step("Arrange: dict с is_active=True"):
            user = {"id": "u1", "role": "student", "is_active": True}

        with autotest.step("Act: вызываем зависимость напрямую"):
            result = require_active_user(current_user=user)

        with autotest.step("Assert: возвращает тот же объект"):
            assert_true(result is user, "тот же dict")

    @autotest.num("1957")
    @autotest.external_id("fd2b3b80-0116-4ef5-92b3-b23626fc27c1")
    @autotest.name("require_active_user: неактивный пользователь → 403")
    def test_fd2b3b80_inactive_raises_403(self):
        with autotest.step("Arrange: dict с is_active=False"):
            user = {"id": "u2", "role": "student", "is_active": False}

        with autotest.step("Act + Assert: ожидаем 403"):
            raised = False
            try:
                require_active_user(current_user=user)
            except HTTPException as exc:
                raised = True
                assert_equal(exc.status_code, 403, "статус 403")
            assert_true(raised, "HTTPException был поднят")


class TestTokenIsActiveRoundTrip:
    @autotest.num("1958")
    @autotest.external_id("362e970f-def2-4815-a07a-bd6f7d870adf")
    @autotest.name("JWT round-trip: is_active=True сохраняется в токене")
    def test_362e970f_is_active_true_round_trip(self):
        from auth.dependencies import decode_backend_token

        with autotest.step("Act: создать токен с is_active=True"):
            token = create_backend_token("u-1958", "student", is_active=True)
            payload = decode_backend_token(token, settings.api.jwt_secret)

        with autotest.step("Assert: is_active=True в payload"):
            assert_true(payload.get("is_active") is True, "is_active=True")

    @autotest.num("1959")
    @autotest.external_id("83f2ecf0-dbd8-4d56-ad9d-20541258de8e")
    @autotest.name("JWT round-trip: is_active=False сохраняется в токене")
    def test_83f2ecf0_is_active_false_round_trip(self):
        from auth.dependencies import decode_backend_token

        with autotest.step("Act: создать токен с is_active=False (дефолт)"):
            token = create_backend_token("u-1959", "student")
            payload = decode_backend_token(token, settings.api.jwt_secret)

        with autotest.step("Assert: is_active=False в payload"):
            assert_true(payload.get("is_active") is False, "is_active=False")


class TestNewUserActivation:
    @pytest.fixture(autouse=True)
    async def setup_db(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Account.__table__.create)
        yield
        await self.engine.dispose()

    @autotest.num("1960")
    @autotest.external_id("38cd1a38-0865-4086-b579-84272e64eded")
    @autotest.name("create_user (credentials): пользователь активен (is_active=True)")
    async def test_38cd1a38_credential_user_is_active(self):
        with autotest.step("Act: создать credential-пользователя"):
            async with self.session_factory() as db:
                user = await create_user(
                    db=db,
                    email=f"cred-{uuid.uuid4()}@test.local",
                    password_hash="hash",
                )

        with autotest.step("Assert: is_active is True (credential-путь активен)"):
            assert_true(user.is_active is True, "credential-пользователь активен")

    @autotest.num("1961")
    @autotest.external_id("a0f6bba4-e63d-48c5-adb5-dd910b3a3831")
    @autotest.name("upsert_github_user (OAuth): новый пользователь is_active=False")
    async def test_a0f6bba4_oauth_user_is_inactive(self):
        with autotest.step("Act: создать OAuth-пользователя через GitHub"):
            async with self.session_factory() as db:
                user = await upsert_github_user(
                    db=db,
                    email=f"gh-{uuid.uuid4()}@test.local",
                    name="GH User",
                    image=None,
                    provider_account_id=str(uuid.uuid4()),
                )

        with autotest.step("Assert: is_active is False"):
            assert_true(user.is_active is False, "новый oauth-пользователь неактивен")


class TestAdminPatchIsActive:
    """PATCH /admin/users/{id}: is_active changes via the admin endpoint."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)

        app = FastAPI()
        app.include_router(admin_router, prefix="/admin")

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        def _override_admin():
            return _ADMIN_USER

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_current_user] = _override_admin
        self.app = app

        async with self.session_factory() as db:
            db.add_all(
                [
                    User(
                        id="u1",
                        name="Alice",
                        email="alice@test.local",
                        role="student",
                        is_active=False,
                    ),
                    User(
                        id="admin-001",
                        name="Admin",
                        email="admin@test.local",
                        role="admin",
                        is_active=True,
                    ),
                ]
            )
            await db.commit()

        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    @autotest.num("1962")
    @autotest.external_id("2dca5dd0-b8fc-4db7-90a0-f08fec473681")
    @autotest.name("PATCH /admin/users/{id}: is_active=True флипает и ответ содержит is_active")
    async def test_2dca5dd0_patch_is_active_flips(self):
        with autotest.step("Act: PATCH is_active=true для u1"):
            async with self._client() as client:
                resp = await client.patch("/admin/users/u1", json={"is_active": True})

        with autotest.step("Assert: 200, is_active=True в ответе"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_true(body["is_active"] is True, "is_active=True")
            assert_equal(body["id"], "u1", "id=u1")


class TestActivateEndpoint:
    """HTTP tests for POST /auth/activate."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Account.__table__.create)

        app = FastAPI()
        app.state.limiter = limiter

        @app.exception_handler(RateLimitExceeded)
        async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
            return JSONResponse(status_code=429, content={"detail": "too many"})

        app.include_router(auth_router, prefix="/auth")

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = _override_db
        self.app = app
        limiter.reset()

        # Seed an inactive user.
        async with self.session_factory() as db:
            db.add(
                User(
                    id="inactive-001",
                    email="inactive@test.local",
                    role="student",
                    is_active=False,
                )
            )
            await db.commit()

        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    def _internal_headers(self) -> dict:
        return {"Authorization": f"Bearer {settings.security.internal_api_token}"}

    @autotest.num("1963")
    @autotest.external_id("68fd3512-9759-4ff8-a21e-2e31cac808a9")
    @autotest.name("POST /auth/activate: без internal token → 401")
    async def test_68fd3512_activate_no_token_returns_401(self):
        with autotest.step("Act: вызываем без Authorization"):
            async with self._client() as client:
                resp = await client.post("/auth/activate", json={"email": "inactive@test.local"})

        with autotest.step("Assert: 401"):
            assert_equal(resp.status_code, 401, "status 401")

    @autotest.num("1964")
    @autotest.external_id("169d16f8-8530-4988-96f1-89aa7de43714")
    @autotest.name("POST /auth/activate: с токеном → пользователь активирован (200)")
    async def test_169d16f8_activate_with_token_succeeds(self):
        with autotest.step("Act: активировать inactive@test.local"):
            async with self._client() as client:
                resp = await client.post(
                    "/auth/activate",
                    json={"email": "inactive@test.local"},
                    headers=self._internal_headers(),
                )

        with autotest.step("Assert: 200, is_active=True"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_true(body["is_active"] is True, "is_active=True")
            assert_equal(body["email"], "inactive@test.local", "email совпадает")

        with autotest.step("Assert: пользователь в БД активен"):
            async with self.session_factory() as db:
                user = await db.get(User, "inactive-001")
            assert_true(user.is_active is True, "is_active в БД = True")

    @autotest.num("1965")
    @autotest.external_id("2e20911e-1c9a-4487-8938-132394f688bd")
    @autotest.name("POST /auth/activate: неизвестный email → 404")
    async def test_2e20911e_activate_unknown_email_returns_404(self):
        with autotest.step("Act: активировать несуществующий email"):
            async with self._client() as client:
                resp = await client.post(
                    "/auth/activate",
                    json={"email": "nobody@test.local"},
                    headers=self._internal_headers(),
                )

        with autotest.step("Assert: 404"):
            assert_equal(resp.status_code, 404, "status 404")
