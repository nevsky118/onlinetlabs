import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in, assert_true
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from auth.dependencies import decode_backend_token
from auth.router import router as auth_router
from config import settings
from db.session import get_db
from models.user import Account, User
from rate_limit import limiter

pytestmark = [pytest.mark.unit, pytest.mark.auth]


class TestAuthRouter:
    @pytest.fixture(autouse=True)
    async def setup(self):
        # SQLite in-memory: создаём только таблицу users, без полной metadata
        # (другие модели содержат JSONB и расширения, которые SQLite не понимает).
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Account.__table__.create)

        # Минимальное приложение только с auth-роутером.
        app = FastAPI()
        app.state.limiter = limiter

        @app.exception_handler(RateLimitExceeded)
        async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
            return JSONResponse(status_code=429, content={"detail": "too many"})

        app.include_router(auth_router, prefix="/auth")

        async def _override_get_db():
            async with self.session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = _override_get_db
        self.app = app

        # Сбрасываем slowapi storage между тестами — общий лимитер хранит
        # счётчики по ключам, что протекало бы из теста в тест.
        limiter.reset()

        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        transport = ASGITransport(app=self.app)
        return AsyncClient(transport=transport, base_url="http://testserver")

    @autotest.num("710")
    @autotest.external_id("11223344-5566-4778-8990-aabbccddeeff")
    @autotest.name("POST /auth/register: успешная регистрация → 201 + UserResponse")
    async def test_11223344_register_success_returns_201(self):
        with autotest.step("Act: регистрируем нового пользователя"):
            async with self._client() as client:
                response = await client.post(
                    "/auth/register",
                    json={
                        "email": "newuser@example.com",
                        "password": "supersecret123",
                        "name": "New User",
                    },
                )

        with autotest.step("Assert: 201 и валидный payload"):
            assert_equal(response.status_code, 201, "status_code = 201")
            body = response.json()
            assert_equal(body["email"], "newuser@example.com", "email")
            assert_equal(body["name"], "New User", "name")
            assert_equal(body["role"], "student", "role по умолчанию")
            assert_in("id", body, "id присутствует")

    @autotest.num("711")
    @autotest.external_id("22334455-6677-4889-8aa1-bbccddeeff00")
    @autotest.name("POST /auth/register: дубликат email → 409")
    async def test_22334455_register_duplicate_returns_409(self):
        with autotest.step("Arrange: создаём первого пользователя"):
            async with self._client() as client:
                first = await client.post(
                    "/auth/register",
                    json={
                        "email": "dup@example.com",
                        "password": "supersecret123",
                    },
                )
                assert_equal(first.status_code, 201, "первая регистрация ok")

        with autotest.step("Act: пытаемся зарегать тот же email"):
            async with self._client() as client:
                response = await client.post(
                    "/auth/register",
                    json={
                        "email": "dup@example.com",
                        "password": "anothersecret",
                    },
                )

        with autotest.step("Assert: 409 conflict"):
            assert_equal(response.status_code, 409, "status_code = 409")

    @autotest.num("712")
    @autotest.external_id("33445566-7788-499a-8bb2-ccddeeff0011")
    @autotest.name("POST /auth/register: короткий пароль → 422")
    async def test_33445566_register_short_password_returns_422(self):
        with autotest.step("Act: пароль из 4 символов (min_length=8)"):
            async with self._client() as client:
                response = await client.post(
                    "/auth/register",
                    json={"email": "short@example.com", "password": "abcd"},
                )

        with autotest.step("Assert: 422 validation error"):
            assert_equal(response.status_code, 422, "status_code = 422")

    @autotest.num("713")
    @autotest.external_id("44556677-8899-4aab-8cc3-ddeeff001122")
    @autotest.name("POST /auth/exchange: валидный INTERNAL_API_TOKEN → JWT")
    async def test_44556677_exchange_valid_internal_token_returns_jwt(self):
        with autotest.step("Arrange: создаём пользователя и узнаём его id"):
            async with self._client() as client:
                reg = await client.post(
                    "/auth/register",
                    json={
                        "email": "exch@example.com",
                        "password": "supersecret123",
                    },
                )
                user_id = reg.json()["id"]

        with autotest.step("Act: запрашиваем exchange с INTERNAL_API_TOKEN"):
            async with self._client() as client:
                response = await client.post(
                    "/auth/exchange",
                    json={"user_id": user_id, "email": "exch@example.com"},
                    headers={"Authorization": (f"Bearer {settings.security.internal_api_token}")},
                )

        with autotest.step("Assert: 200 + декодируемый JWT с sub = user_id"):
            assert_equal(response.status_code, 200, "status_code = 200")
            body = response.json()
            assert_equal(body["token_type"], "bearer", "token_type")
            payload = decode_backend_token(body["access_token"], settings.api.jwt_secret)
            assert_equal(payload["sub"], user_id, "sub claim = user_id")
            assert_equal(payload["role"], "student", "role claim")

    @autotest.num("714")
    @autotest.external_id("55667788-99aa-4bbc-8dd4-eeff00112233")
    @autotest.name("POST /auth/exchange: неверный internal token → 401")
    async def test_55667788_exchange_bad_internal_token_returns_401(self):
        with autotest.step("Act: вызываем exchange с мусорным Bearer"):
            async with self._client() as client:
                response = await client.post(
                    "/auth/exchange",
                    json={"user_id": "anything", "email": "x@example.com"},
                    headers={"Authorization": "Bearer not-the-real-token"},
                )

        with autotest.step("Assert: 401 invalid internal token"):
            assert_equal(response.status_code, 401, "status_code = 401")
            assert_true(
                "internal" in response.json()["detail"].lower(),
                "detail упоминает internal",
            )
