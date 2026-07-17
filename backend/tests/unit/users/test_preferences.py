"""Тесты GET/PATCH /users/me/preferences."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from auth.dependencies import get_current_user
from db.session import get_db
from models.user import User
from users.router import router as users_router

pytestmark = [pytest.mark.unit]

_VALID_MODEL_ID = "yandex-gpt-5.1"

_USER_NO_SELECT = {"id": "user-ns", "role": "student", "can_select": False}
_USER_CAN_SELECT = {"id": "user-cs", "role": "student", "can_select": True}


class TestPreferencesEndpoints:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)

        async with self.session_factory() as db:
            db.add_all(
                [
                    User(id="user-ns", name="NoSelect", email="nosel@test.local", role="student"),
                    User(id="user-cs", name="CanSelect", email="cansel@test.local", role="student"),
                ]
            )
            await db.commit()

        self.app_no_select = self._build_app(_USER_NO_SELECT)
        self.app_can_select = self._build_app(_USER_CAN_SELECT)

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

    def _client(self, can_select: bool = False) -> AsyncClient:
        app = self.app_can_select if can_select else self.app_no_select
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")

    @autotest.num("1951")
    @autotest.external_id("25b65c19-8400-4f3a-8b44-e4aba61753a6")
    @autotest.name("GET /preferences: свежий пользователь → default_model_id=null")
    async def test_25b65c19_get_fresh_user_null(self):
        with autotest.step("Act: GET /users/me/preferences"):
            async with self._client() as client:
                resp = await client.get("/users/me/preferences")

        with autotest.step("Assert: 200, default_model_id=null"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_true(resp.json()["default_model_id"] is None, "default_model_id=null")

    @autotest.num("1952")
    @autotest.external_id("a5ca6174-c766-4407-8ac5-ce62d3230244")
    @autotest.name("PATCH /preferences: {default_model_id: null} → 200, остаётся null")
    async def test_a5ca6174_patch_null_stays_null(self):
        with autotest.step("Act: PATCH с null"):
            async with self._client() as client:
                resp = await client.patch("/users/me/preferences", json={"default_model_id": None})

        with autotest.step("Assert: 200, default_model_id=null"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_true(resp.json()["default_model_id"] is None, "default_model_id=null")

    @autotest.num("1953")
    @autotest.external_id("ab755754-b990-4bbc-be8b-f7234e56ee77")
    @autotest.name("PATCH /preferences: неизвестная модель с can_select=True → 422")
    async def test_ab755754_invalid_model_422(self):
        with autotest.step("Act: PATCH с несуществующей моделью"):
            async with self._client(can_select=True) as client:
                resp = await client.patch(
                    "/users/me/preferences",
                    json={"default_model_id": "nonexistent-model-xyz"},
                )

        with autotest.step("Assert: 422"):
            assert_equal(resp.status_code, 422, "status 422")

    @autotest.num("1954")
    @autotest.external_id("3d094843-791e-454a-abba-d0b9b0f364c6")
    @autotest.name("PATCH /preferences: валидная модель с can_select=False → 403")
    async def test_3d094843_valid_model_no_permission_403(self):
        with autotest.step("Act: PATCH с can_select=False"):
            async with self._client(can_select=False) as client:
                resp = await client.patch(
                    "/users/me/preferences",
                    json={"default_model_id": _VALID_MODEL_ID},
                )

        with autotest.step("Assert: 403"):
            assert_equal(resp.status_code, 403, "status 403")

    @autotest.num("1955")
    @autotest.external_id("64428791-cc9b-4da1-89c6-375fe448adfc")
    @autotest.name("PATCH /preferences: валидная модель с can_select=True → 200, сохранено")
    async def test_64428791_valid_model_persisted(self):
        with autotest.step("Act: PATCH с can_select=True"):
            async with self._client(can_select=True) as client:
                resp = await client.patch(
                    "/users/me/preferences",
                    json={"default_model_id": _VALID_MODEL_ID},
                )

        with autotest.step("Assert: 200, default_model_id сохранён"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_equal(resp.json()["default_model_id"], _VALID_MODEL_ID, "модель сохранена")

        with autotest.step("Assert: GET возвращает сохранённое значение"):
            async with self._client(can_select=True) as client:
                get_resp = await client.get("/users/me/preferences")
            assert_equal(get_resp.status_code, 200, "GET 200")
            assert_equal(
                get_resp.json()["default_model_id"], _VALID_MODEL_ID, "GET возвращает модель"
            )
