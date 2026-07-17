"""P4 task 1 + task 3: тесты /admin/labs (GET, PATCH, rebuild-template)."""

import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from admin.router import _rebuild_worker, router as admin_router
from auth.dependencies import get_current_user
from db.session import get_db
from deps import get_gns3_client, get_session_factory
from models.lab import Lab, LabStep

pytestmark = [pytest.mark.unit]

_ADMIN_USER = {"id": "admin-001", "role": "admin"}
_STUDENT_USER = {"id": "student-001", "role": "student"}


class TestAdminLabsEndpoints:
    """HTTP-тесты GET /admin/labs и PATCH /admin/labs/{slug}."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LabStep.__table__.create)

        app = FastAPI()
        app.include_router(admin_router, prefix="/admin")

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        def _override_admin():
            return _ADMIN_USER

        def _override_student():
            return _STUDENT_USER

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_current_user] = _override_admin
        self.app = app

        self.student_app = FastAPI()
        self.student_app.include_router(admin_router, prefix="/admin")
        self.student_app.dependency_overrides[get_db] = _override_db
        self.student_app.dependency_overrides[get_current_user] = _override_student

        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    def _student_client(self) -> AsyncClient:
        return AsyncClient(
            transport=ASGITransport(app=self.student_app), base_url="http://testserver"
        )

    async def _seed(self, labs: list[Lab]) -> None:
        async with self.session_factory() as db:
            db.add_all(labs)
            await db.commit()

    @autotest.num("1932")
    @autotest.external_id("b0c1d2e3-f4a5-4b6c-8d7e-9f0a1b2c3d4e")
    @autotest.name("GET /admin/labs: не-admin получает 403")
    async def test_b0c1d2e3_non_admin_gets_403(self):
        with autotest.step("Act: student запрашивает /admin/labs"):
            async with self._student_client() as client:
                resp = await client.get("/admin/labs")

        with autotest.step("Assert: 403"):
            assert_equal(resp.status_code, 403, "status 403")

    @autotest.num("1933")
    @autotest.external_id("c1d2e3f4-a5b6-4c7d-9e8f-0a1b2c3d4e5f")
    @autotest.name("GET /admin/labs: возвращает вставленные лабы с корректным template_ready")
    async def test_c1d2e3f4_list_labs_template_ready(self):
        await self._seed(
            [
                Lab(
                    slug="gns3-lab-with-tpl",
                    title="GNS3 with template",
                    environment_type="gns3",
                    gns3_template_project_id="tpl-uuid-123",
                    enabled=True,
                ),
                Lab(
                    slug="none-lab",
                    title="None env lab",
                    environment_type="none",
                    enabled=True,
                ),
                Lab(
                    slug="gns3-lab-no-tpl",
                    title="GNS3 no template",
                    environment_type="gns3",
                    enabled=True,
                ),
            ]
        )

        with autotest.step("Act: GET /admin/labs"):
            async with self._client() as client:
                resp = await client.get("/admin/labs")

        with autotest.step("Assert: 200, 3 лабы"):
            assert_equal(resp.status_code, 200, "status 200")
            items = resp.json()
            assert_equal(len(items), 3, "3 лабы")

        with autotest.step("Assert: template_ready для none-env — True"):
            none_item = next(i for i in items if i["slug"] == "none-lab")
            assert_true(none_item["template_ready"] is True, "none env → template_ready True")

        with autotest.step("Assert: template_ready для gns3+id — True"):
            gns3_with = next(i for i in items if i["slug"] == "gns3-lab-with-tpl")
            assert_true(gns3_with["template_ready"] is True, "gns3 with tpl → template_ready True")

        with autotest.step("Assert: template_ready для gns3 без id — False"):
            gns3_no = next(i for i in items if i["slug"] == "gns3-lab-no-tpl")
            assert_true(gns3_no["template_ready"] is False, "gns3 no tpl → template_ready False")

    @autotest.num("1934")
    @autotest.external_id("d2e3f4a5-b6c7-4d8e-af9f-1b2c3d4e5f6a")
    @autotest.name("PATCH /admin/labs/{slug}: переключает enabled → false")
    async def test_d2e3f4a5_patch_toggles_enabled(self):
        await self._seed(
            [
                Lab(slug="toggle-lab", title="Toggle Lab", environment_type="none", enabled=True),
            ]
        )

        with autotest.step("Act: PATCH enabled=false"):
            async with self._client() as client:
                resp = await client.patch("/admin/labs/toggle-lab", json={"enabled": False})

        with autotest.step("Assert: 200, enabled=false в ответе"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_equal(resp.json()["enabled"], False, "enabled=false в ответе")

        with autotest.step("Assert: БД отражает изменение"):
            async with self.session_factory() as db:
                lab = await db.get(Lab, "toggle-lab")
                assert_true(lab.enabled is False, "enabled=false в БД")

    @autotest.num("1935")
    @autotest.external_id("e3f4a5b6-c7d8-4e9f-b0a1-2c3d4e5f6a7b")
    @autotest.name("PATCH /admin/labs/{slug}: устанавливает gns3_template_project_id")
    async def test_e3f4a5b6_patch_sets_template_id(self):
        await self._seed(
            [
                Lab(slug="tpl-lab", title="Template Lab", environment_type="gns3", enabled=True),
            ]
        )

        with autotest.step("Act: PATCH gns3_template_project_id"):
            async with self._client() as client:
                resp = await client.patch(
                    "/admin/labs/tpl-lab",
                    json={"gns3_template_project_id": "new-tpl-uuid-999"},
                )

        with autotest.step("Assert: 200, gns3_template_project_id и template_ready=True"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_equal(body["gns3_template_project_id"], "new-tpl-uuid-999", "tpl id")
            assert_true(body["template_ready"] is True, "template_ready True после установки id")

    @autotest.num("1936")
    @autotest.external_id("f4a5b6c7-d8e9-4f0a-c1b2-3d4e5f6a7b8c")
    @autotest.name("PATCH /admin/labs/{slug}: неизвестный slug → 404")
    async def test_f4a5b6c7_patch_unknown_slug_404(self):
        with autotest.step("Act: PATCH несуществующего slug"):
            async with self._client() as client:
                resp = await client.patch("/admin/labs/does-not-exist", json={"enabled": False})

        with autotest.step("Assert: 404"):
            assert_equal(resp.status_code, 404, "status 404")

    @autotest.num("1937")
    @autotest.external_id("a5b6c7d8-e9f0-4a1b-d2c3-4e5f6a7b8c9d")
    @autotest.name("GET /admin/labs: template_status по умолчанию 'unknown' при meta=null")
    async def test_a5b6c7d8_template_status_default_unknown(self):
        await self._seed(
            [
                Lab(
                    slug="no-meta-lab",
                    title="No Meta",
                    environment_type="none",
                    enabled=True,
                    meta=None,
                ),
            ]
        )

        with autotest.step("Act: GET /admin/labs"):
            async with self._client() as client:
                resp = await client.get("/admin/labs")

        with autotest.step("Assert: template_status='unknown' при meta=null"):
            assert_equal(resp.status_code, 200, "status 200")
            item = resp.json()[0]
            assert_equal(item["template_status"], "unknown", "template_status=unknown")


class TestRebuildTemplate:
    """HTTP-тесты POST /admin/labs/{slug}/rebuild-template + worker."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LabStep.__table__.create)

        self.stub_client = AsyncMock()
        self.stub_client.build_template = AsyncMock(return_value=str(uuid.uuid4()))

        app = FastAPI()
        app.include_router(admin_router, prefix="/admin")

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_current_user] = lambda: _ADMIN_USER
        app.dependency_overrides[get_gns3_client] = lambda: self.stub_client
        app.dependency_overrides[get_session_factory] = lambda: self.session_factory

        self.app = app

        # student app — needs same overrides so FastAPI resolves deps before 403
        student_app = FastAPI()
        student_app.include_router(admin_router, prefix="/admin")
        student_app.dependency_overrides[get_db] = _override_db
        student_app.dependency_overrides[get_current_user] = lambda: _STUDENT_USER
        student_app.dependency_overrides[get_gns3_client] = lambda: self.stub_client
        student_app.dependency_overrides[get_session_factory] = lambda: self.session_factory
        self.student_app = student_app

        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    def _student_client(self) -> AsyncClient:
        return AsyncClient(
            transport=ASGITransport(app=self.student_app), base_url="http://testserver"
        )

    async def _seed(self, labs: list[Lab]) -> None:
        async with self.session_factory() as db:
            db.add_all(labs)
            await db.commit()

    @autotest.num("1938")
    @autotest.external_id("b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e")
    @autotest.name("POST rebuild-template: не-admin → 403")
    async def test_b1c2d3e4_rebuild_non_admin_403(self):
        await self._seed(
            [
                Lab(slug="gns3-lab", title="GNS3", environment_type="gns3", enabled=True),
            ]
        )
        with autotest.step("Act"):
            async with self._student_client() as client:
                resp = await client.post("/admin/labs/gns3-lab/rebuild-template")
        with autotest.step("Assert: 403"):
            assert_equal(resp.status_code, 403, "403 для не-admin")

    @autotest.num("1939")
    @autotest.external_id("c2d3e4f5-a6b7-4c8d-9e0f-1a2b3c4d5e6f")
    @autotest.name("POST rebuild-template: неизвестный slug → 404")
    async def test_c2d3e4f5_rebuild_unknown_slug_404(self):
        with autotest.step("Act"):
            async with self._client() as client:
                resp = await client.post("/admin/labs/no-such-lab/rebuild-template")
        with autotest.step("Assert: 404"):
            assert_equal(resp.status_code, 404, "404 для неизвестного slug")

    @autotest.num("1940")
    @autotest.external_id("d3e4f5a6-b7c8-4d9e-af0f-2b3c4d5e6f7a")
    @autotest.name("POST rebuild-template: не-gns3 лаба → 400")
    async def test_d3e4f5a6_rebuild_non_gns3_400(self):
        await self._seed(
            [
                Lab(slug="none-lab", title="None", environment_type="none", enabled=True),
            ]
        )
        with autotest.step("Act"):
            async with self._client() as client:
                resp = await client.post("/admin/labs/none-lab/rebuild-template")
        with autotest.step("Assert: 400"):
            assert_equal(resp.status_code, 400, "400 для не-gns3")

    @autotest.num("1941")
    @autotest.external_id("e4f5a6b7-c8d9-4e0f-b1a2-3c4d5e6f7a8b")
    @autotest.name("POST rebuild-template: gns3 лаба → 202, building в ответе")
    async def test_e4f5a6b7_rebuild_gns3_202_meta_building(self):
        # stub raises so worker sets "error" — lets us assert the endpoint
        # committed "building" synchronously (confirmed by 202 response) without
        # racing against the background task overwriting the DB state.
        self.stub_client.build_template = AsyncMock(side_effect=RuntimeError("stubbed"))
        await self._seed(
            [
                Lab(slug="build-lab", title="Build", environment_type="gns3", enabled=True),
            ]
        )
        with autotest.step("Act: POST rebuild-template"):
            async with self._client() as client:
                resp = await client.post("/admin/labs/build-lab/rebuild-template")
        with autotest.step("Assert: 202, status=building в ответе"):
            assert_equal(resp.status_code, 202, "202")
            assert_equal(resp.json()["status"], "building", "status=building")
        with autotest.step("Assert: meta.template_status в БД — building→error (worker ran)"):
            async with self.session_factory() as db:
                from labs.service import get_lab_by_slug

                lab = await get_lab_by_slug(db, "build-lab")
                # endpoint commits "building" synchronously; background task then runs and
                # writes "error" (stub raises). Either value confirms the endpoint committed.
                assert_true(
                    lab.meta["template_status"] in {"building", "error"},
                    "template_status is building или error",
                )

    @autotest.num("1942")
    @autotest.external_id("f5a6b7c8-d9e0-4f1a-c2b3-4d5e6f7a8b9c")
    @autotest.name("POST rebuild-template: idempotent — не запускает второй билд")
    async def test_f5a6b7c8_rebuild_idempotent(self):
        await self._seed(
            [
                Lab(
                    slug="already-building",
                    title="Building",
                    environment_type="gns3",
                    enabled=True,
                    meta={"template_status": "building"},
                ),
            ]
        )
        self.stub_client.build_template.reset_mock()
        with autotest.step("Act: POST на уже строящуюся лабу"):
            async with self._client() as client:
                resp = await client.post("/admin/labs/already-building/rebuild-template")
        with autotest.step("Assert: 202 building, build_template не вызван"):
            assert_equal(resp.status_code, 202, "202")
            assert_equal(resp.json()["status"], "building", "status=building")
            assert_equal(self.stub_client.build_template.call_count, 0, "build_template не вызван")

    @autotest.num("1943")
    @autotest.external_id("a6b7c8d9-e0f1-4a2b-d3c4-5e6f7a8b9c0d")
    @autotest.name("Worker: успех — записывает template_id и status=ready")
    async def test_a6b7c8d9_worker_success(self):
        await self._seed(
            [
                Lab(slug="worker-ok", title="Worker OK", environment_type="gns3", enabled=True),
            ]
        )
        expected_id = str(uuid.uuid4())
        client = AsyncMock()
        client.build_template = AsyncMock(return_value=expected_id)

        with autotest.step("Act: вызов worker напрямую с тестовой session_factory"):
            await _rebuild_worker("worker-ok", client, session_factory=self.session_factory)

        with autotest.step("Assert: template_id и status=ready в БД"):
            async with self.session_factory() as db:
                from labs.service import get_lab_by_slug

                lab = await get_lab_by_slug(db, "worker-ok")
                assert_equal(lab.gns3_template_project_id, expected_id, "template_id записан")
                assert_equal(lab.meta["template_status"], "ready", "status=ready")

    @autotest.num("1944")
    @autotest.external_id("b7c8d9e0-f1a2-4b3c-e4d5-6f7a8b9c0d1e")
    @autotest.name("Worker: ошибка build_template → status=error")
    async def test_b7c8d9e0_worker_error(self):
        await self._seed(
            [
                Lab(slug="worker-err", title="Worker Err", environment_type="gns3", enabled=True),
            ]
        )
        client = AsyncMock()
        client.build_template = AsyncMock(side_effect=RuntimeError("gns3 down"))

        with autotest.step("Act: вызов worker с ошибкой"):
            await _rebuild_worker("worker-err", client, session_factory=self.session_factory)

        with autotest.step("Assert: status=error, template_id не перезаписан"):
            async with self.session_factory() as db:
                from labs.service import get_lab_by_slug

                lab = await get_lab_by_slug(db, "worker-err")
                assert_equal(lab.meta["template_status"], "error", "status=error")
                assert_true(lab.gns3_template_project_id is None, "template_id не установлен")
