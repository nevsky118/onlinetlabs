"""Тесты GET /users/me/consent."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from auth.dependencies import get_current_user
from control_interface.consent import grant, revoke
from control_interface.router import router as consent_router
from db.session import get_db
from models.consent import Consent
from models.user import User

pytestmark = [pytest.mark.unit]

_USER = {"id": "user-consent-test", "role": "student"}


class TestConsentGet:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Consent.__table__.create)

        async with self.session_factory() as db:
            db.add(
                User(id="user-consent-test", name="Test", email="test@test.local", role="student")
            )
            await db.commit()

        app = FastAPI()
        app.include_router(consent_router, prefix="/users/me")

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_current_user] = lambda: _USER
        self.app = app

        # Приложение без аутентификации (dependency_overrides не переопределяет get_current_user)
        self.unauth_app = FastAPI()
        self.unauth_app.include_router(consent_router, prefix="/users/me")
        self.unauth_app.dependency_overrides[get_db] = _override_db

        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    def _unauth_client(self) -> AsyncClient:
        return AsyncClient(
            transport=ASGITransport(app=self.unauth_app), base_url="http://testserver"
        )

    @autotest.num("1949")
    @autotest.external_id("48fe4a5d-8f48-44d1-9d89-a63d220acd29")
    @autotest.name("GET /consent: без аутентификации → 401/403")
    async def test_48fe4a5d_unauthenticated_rejected(self):
        with autotest.step("Act: GET /users/me/consent без токена"):
            async with self._unauth_client() as client:
                resp = await client.get("/users/me/consent")

        with autotest.step("Assert: 401 или 403"):
            assert_true(
                resp.status_code in (401, 403), f"ожидали 401/403, получили {resp.status_code}"
            )

    @autotest.num("1950")
    @autotest.external_id("99ff576e-a9d6-44b9-a721-26b4ca3736b0")
    @autotest.name("GET /consent: возвращает только активные (не отозванные) согласия")
    async def test_99ff576e_returns_only_active_consents(self):
        async with self.session_factory() as db:
            await grant(db, "user-consent-test", "study", observe=True, act=True)
            await grant(db, "user-consent-test", "product", observe=True, act=False)
            await revoke(db, "user-consent-test", "product")

        with autotest.step("Act: GET /users/me/consent"):
            async with self._client() as client:
                resp = await client.get("/users/me/consent")

        with autotest.step("Assert: 200, только study (product отозван)"):
            assert_equal(resp.status_code, 200, "status 200")
            items = resp.json()
            assert_equal(len(items), 1, "одно активное согласие")
            assert_equal(items[0]["scope"], "study", "scope=study")
            assert_equal(items[0]["observe"], True, "observe=True")
            assert_equal(items[0]["act"], True, "act=True")
            assert_true("granted_at" in items[0], "granted_at присутствует")
