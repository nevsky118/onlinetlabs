"""Tests for POST /internal/labs/{slug}/gns3-template."""

import pytest
from fastapi import FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from auth.dependencies import require_internal_caller
from db.session import get_db
from labs.router import internal_router
from models.lab import Lab

pytestmark = [pytest.mark.unit]

_TOKEN = "test-internal-token"
_HEADERS_OK = {"Authorization": f"Bearer {_TOKEN}"}
_HEADERS_BAD = {"Authorization": "Bearer wrong-token"}


async def _build_app() -> tuple[FastAPI, async_sessionmaker]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Lab.__table__.create)

    app = FastAPI()
    app.include_router(internal_router, prefix="/internal")

    async def _override_db():
        async with session_factory() as db:
            yield db

    def _override_token_ok():
        return None

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[require_internal_caller] = _override_token_ok
    return app, session_factory


class TestInternalLabTemplate:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Lab.__table__.create)

        self.app = FastAPI()
        self.app.include_router(internal_router, prefix="/internal")

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        def _override_token_ok():
            return None

        self.app.dependency_overrides[get_db] = _override_db
        self.app.dependency_overrides[require_internal_caller] = _override_token_ok

        # app без override токена — для проверки 401
        self.raw_app = FastAPI()
        self.raw_app.include_router(internal_router, prefix="/internal")
        self.raw_app.dependency_overrides[get_db] = _override_db

        async with self.session_factory() as db:
            db.add(
                Lab(
                    slug="ospf-lab",
                    title="OSPF Lab",
                    difficulty="beginner",
                    environment_type="gns3",
                )
            )
            await db.commit()

        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    def _raw_client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.raw_app), base_url="http://testserver")

    @autotest.num("1826")
    @autotest.external_id("8a0aea6c-53cb-4732-ac7c-811a7291a533")
    @autotest.name("POST /internal/labs/{slug}/gns3-template: default variant — 200, поле записано")
    async def test_8a0aea6c_set_default_template(self):
        with autotest.step("Act: POST с variant=default"):
            async with self._client() as client:
                resp = await client.post(
                    "/internal/labs/ospf-lab/gns3-template",
                    json={"template_project_id": "proj-uuid-default"},
                )

        with autotest.step("Assert: 200"):
            assert_equal(resp.status_code, 200, "status 200")

        with autotest.step("Assert: gns3_template_project_id установлен"):
            body = resp.json()
            assert_equal(body["slug"], "ospf-lab", "slug")
            assert_equal(body["gns3_template_project_id"], "proj-uuid-default", "default field")

        with autotest.step("Assert: остальные поля пустые"):
            assert_true(body["gns3_template_project_id_frr"] is None, "frr=None")
            assert_true(body["gns3_template_project_id_iosvl2"] is None, "iosvl2=None")

    @autotest.num("1827")
    @autotest.external_id("9a08f49c-7e89-4ab4-afc4-be6c0261f3ba")
    @autotest.name("POST /internal/labs/{slug}/gns3-template: variant=frr — поле _frr записано")
    async def test_9a08f49c_set_frr_template(self):
        with autotest.step("Act: POST с variant=frr"):
            async with self._client() as client:
                resp = await client.post(
                    "/internal/labs/ospf-lab/gns3-template",
                    json={"template_project_id": "proj-uuid-frr", "variant": "frr"},
                )

        with autotest.step("Assert: 200"):
            assert_equal(resp.status_code, 200, "status 200")

        with autotest.step("Assert: gns3_template_project_id_frr установлен"):
            body = resp.json()
            assert_equal(body["gns3_template_project_id_frr"], "proj-uuid-frr", "frr field")

        with autotest.step("Assert: default и iosvl2 пусты"):
            assert_true(body["gns3_template_project_id"] is None, "default=None")
            assert_true(body["gns3_template_project_id_iosvl2"] is None, "iosvl2=None")

    @autotest.num("1828")
    @autotest.external_id("cb7a90b6-f065-48a0-9576-e548bf0a88be")
    @autotest.name("POST /internal/labs/{slug}/gns3-template: неверный токен — 401")
    async def test_cb7a90b6_invalid_token_rejected(self):
        with autotest.step("Act: POST с неверным Bearer токеном"):
            async with self._raw_client() as client:
                resp = await client.post(
                    "/internal/labs/ospf-lab/gns3-template",
                    json={"template_project_id": "proj-uuid-bad"},
                    headers=_HEADERS_BAD,
                )

        with autotest.step("Assert: 401"):
            assert_equal(resp.status_code, 401, "status 401")

    @autotest.num("1829")
    @autotest.external_id("e4e9cf7e-bf00-44a5-8ef4-98ce41a4d975")
    @autotest.name("POST /internal/labs/{slug}/gns3-template: неизвестный slug — 404")
    async def test_e4e9cf7e_unknown_slug_404(self):
        with autotest.step("Act: POST с несуществующим slug"):
            async with self._client() as client:
                resp = await client.post(
                    "/internal/labs/nonexistent-lab/gns3-template",
                    json={"template_project_id": "proj-uuid-any"},
                )

        with autotest.step("Assert: 404"):
            assert_equal(resp.status_code, 404, "status 404")

        with autotest.step("Assert: detail содержит 'not found'"):
            detail = resp.json().get("detail", "").lower()
            assert_true("not found" in detail, "detail=not found")
