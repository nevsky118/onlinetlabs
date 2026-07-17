"""Task 2: tests for the admin router's pure builders (without spinning up FastAPI)."""

import datetime
import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from admin.data_registry import ADMIN_TABLES
from admin.router import router as admin_router
from auth.dependencies import get_current_user
from db.session import get_db
from models.mcp_audit import MCPAudit
from models.user import User

pytestmark = [pytest.mark.unit]


class TestAdminEndpoints:
    @autotest.num("1810")
    @autotest.external_id("a3f7c2d1-8b4e-4f9a-bc12-5e6d0f1a2b3c")
    @autotest.name("admin: identifier-eval форма ответа на синтетике")
    def test_a3f7c2d1_identifier_eval_shape(self):
        from admin.router import build_identifier_eval

        with autotest.step("Act: собрать eval на синтетике"):
            out = build_identifier_eval()

        with autotest.step("Assert: есть curve, J-оптимум, матрица, first-match, preliminary"):
            for k in ("curve", "j_optimal_t_k", "confusion", "first_match", "preliminary"):
                assert_in(k, out, k)

        with autotest.step("Assert: preliminary=True для синтетики"):
            assert_true(out["preliminary"] is True, "синтетика → предварительно")

        with autotest.step("Assert: curve непуста и содержит нужные поля"):
            assert_true(len(out["curve"]) > 0, "кривая не пуста")
            for field in ("t_k", "latency_median", "false_per_hour", "recall", "j"):
                assert_in(field, out["curve"][0], field)

        with autotest.step("Assert: confusion — словарь со строковыми ключами"):
            assert_true(isinstance(out["confusion"], dict), "confusion — dict")

        with autotest.step("Assert: first_match содержит multi_match_rate"):
            assert_in("multi_match_rate", out["first_match"], "first_match.multi_match_rate")

    @autotest.num("1811")
    @autotest.external_id("0955923d-b23e-4776-b7a0-8552600260f7")
    @autotest.name("admin: tk-sensitivity форма ответа")
    def test_0955923d_tk_sensitivity_shape(self):
        from admin.router import build_tk_sensitivity

        with autotest.step("Act: собрать кривую чувствительности"):
            out = build_tk_sensitivity()

        with autotest.step("Assert: есть points и costs"):
            assert_in("points", out, "points")
            assert_in("costs", out, "costs")

        with autotest.step("Assert: points непуст, каждая точка — ratio/t_k/J"):
            assert_true(len(out["points"]) > 0, "хотя бы одна точка")
            for pt in out["points"]:
                for field in ("ratio", "t_k", "J"):
                    assert_in(field, pt, field)

        with autotest.step("Assert: costs содержит c_stuck и c_intervention"):
            assert_in("c_stuck", out["costs"], "costs.c_stuck")
            assert_in("c_intervention", out["costs"], "costs.c_intervention")

    @autotest.num("1812")
    @autotest.external_id("29876633-d902-47ca-9f2a-54b43167b0df")
    @autotest.name(
        "admin: build_overview пустая БД — возвращает dict с ключами ab/cohort/identifier/ops"
    )
    async def test_29876633_overview_empty_db(self, empty_admin_db):
        from admin.router import build_overview

        with autotest.step("Act: build_overview на пустой БД"):
            out = await build_overview(empty_admin_db)

        with autotest.step("Assert: все верхнеуровневые ключи присутствуют"):
            for k in ("ab", "cohort", "identifier", "ops"):
                assert_in(k, out, k)

        with autotest.step("Assert: ab содержит l2_pass_closed/open/mentor_hours_saved"):
            for k in ("l2_pass_closed", "l2_pass_open", "mentor_hours_saved"):
                assert_in(k, out["ab"], k)

        with autotest.step("Assert: ops.active_sessions >= 0"):
            assert_true(out["ops"]["active_sessions"] >= 0, "active_sessions неотрицателен")

    @autotest.num("1813")
    @autotest.external_id("68b00e53-5e40-4fe2-9a62-0a64855fff33")
    @autotest.name("admin: build_overview с одной метрикой — не падает, возвращает числа")
    async def test_68b00e53_overview_with_seed(self, seeded_admin_db):
        from admin.router import build_overview

        with autotest.step("Act: build_overview с сидом"):
            out = await build_overview(seeded_admin_db)

        with autotest.step("Assert: структура полная"):
            for k in ("ab", "cohort", "identifier", "ops"):
                assert_in(k, out, k)

        with autotest.step("Assert: ops.labeled_real_n >= 1"):
            assert_true(out["ops"]["labeled_real_n"] >= 1, "хотя бы одна метрика")

    @autotest.num("1814")
    @autotest.external_id("e9e284ed-16e2-4481-a76e-908aef728a03")
    @autotest.name("admin: роутер зарегистрирован под /admin в main.py")
    def test_e9e284ed_router_registered(self):
        with autotest.step("Импортировать admin_router"):
            from admin.router import router as admin_router

        with autotest.step("Assert: роутер имеет пути overview/identifier-eval/tk-sensitivity"):
            paths = {r.path for r in admin_router.routes}
            assert_in("/overview", paths, "/overview")
            assert_in("/identifier-eval", paths, "/identifier-eval")
            assert_in("/tk-sensitivity", paths, "/tk-sensitivity")

    @autotest.num("1815")
    @autotest.external_id("45ff77c3-a01a-4b80-865d-e89b51b6d9d3")
    @autotest.name("admin: require_admin отклоняет не-admin (403)")
    def test_45ff77c3_require_admin_rejects(self):
        from fastapi import HTTPException

        from admin.router import require_admin

        with autotest.step("Вызвать require_admin с ролью student"):
            raised = False
            try:
                require_admin(current_user={"role": "student"})
            except HTTPException as exc:
                raised = True
                assert_equal(exc.status_code, 403, "статус 403")

        with autotest.step("Assert: исключение было поднято"):
            assert_true(raised, "HTTPException был поднят для non-admin")


_ADMIN_USER = {"id": "admin-001", "role": "admin"}
_STUDENT_USER = {"id": "student-001", "role": "student"}


class TestAdminUsersEndpoints:
    """HTTP tests for GET /admin/users and PATCH /admin/users/{id}."""

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

        def _override_student():
            return _STUDENT_USER

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_current_user] = _override_admin
        self.app = app
        self.student_app = FastAPI()
        self.student_app.include_router(admin_router, prefix="/admin")
        self.student_app.dependency_overrides[get_db] = _override_db
        self.student_app.dependency_overrides[get_current_user] = _override_student

        # Seed test users.
        async with self.session_factory() as db:
            db.add_all(
                [
                    User(id="u1", name="Alice", email="alice@test.local", role="student"),
                    User(id="u2", name="Bob", email="bob@test.local", role="instructor"),
                    User(id="u3", name="Charlie", email="charlie@test.local", role="admin"),
                    User(
                        id="admin-001", name="AdminSelf", email="adminself@test.local", role="admin"
                    ),
                    User(id="student-001", name="Stu", email="stu@test.local", role="student"),
                ]
            )
            await db.commit()

        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    def _student_client(self) -> AsyncClient:
        return AsyncClient(
            transport=ASGITransport(app=self.student_app), base_url="http://testserver"
        )

    @autotest.num("1816")
    @autotest.external_id("db69554e-095b-4514-9f8c-6a747357d073")
    @autotest.name("GET /admin/users: пагинация и total")
    async def test_db69554e_list_pagination_and_total(self):
        with autotest.step("Act: запросить страницу 1 из 2 пользователей"):
            async with self._client() as client:
                resp = await client.get("/admin/users?page=1&page_size=2")

        with autotest.step("Assert: 200, items=2, total=5"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_equal(body["page"], 1, "page=1")
            assert_equal(body["page_size"], 2, "page_size=2")
            assert_equal(body["total"], 5, "total=5")
            assert_equal(len(body["items"]), 2, "items len=2")

    @autotest.num("1817")
    @autotest.external_id("8b4bdaf0-a21f-488b-827c-6267e08671d8")
    @autotest.name("GET /admin/users: сортировка по email desc")
    async def test_8b4bdaf0_list_sort_email_desc(self):
        with autotest.step("Act: сортировать по email desc"):
            async with self._client() as client:
                resp = await client.get("/admin/users?sort=email&order=desc&page_size=100")

        with autotest.step("Assert: 200, первый email лексически наибольший"):
            assert_equal(resp.status_code, 200, "status 200")
            emails = [item["email"] for item in resp.json()["items"]]
            assert_true(emails == sorted(emails, reverse=True), "desc order")

    @autotest.num("1818")
    @autotest.external_id("2273c58d-4502-46ca-8838-418cf711be5c")
    @autotest.name("GET /admin/users: поиск по имени")
    async def test_2273c58d_list_search_by_name(self):
        with autotest.step("Act: поиск search=Alice"):
            async with self._client() as client:
                resp = await client.get("/admin/users?search=Alice")

        with autotest.step("Assert: возвращает только Alice"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_equal(body["total"], 1, "total=1")
            assert_equal(body["items"][0]["name"], "Alice", "name=Alice")

    @autotest.num("1819")
    @autotest.external_id("44130398-adf2-4add-b7eb-f603485c1548")
    @autotest.name("GET /admin/users: фильтр по роли")
    async def test_44130398_list_filter_by_role(self):
        with autotest.step("Act: filter role=instructor"):
            async with self._client() as client:
                resp = await client.get("/admin/users?role=instructor")

        with autotest.step("Assert: только instructor-пользователи"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_equal(body["total"], 1, "total=1")
            assert_equal(body["items"][0]["role"], "instructor", "role=instructor")

    @autotest.num("1820")
    @autotest.external_id("bb8ea7eb-a00a-42b4-9e39-c2b8747c4a92")
    @autotest.name("PATCH /admin/users/{id}: смена роли — успех")
    async def test_bb8ea7eb_patch_role_success(self):
        with autotest.step("Act: сменить роль u1 на instructor"):
            async with self._client() as client:
                resp = await client.patch("/admin/users/u1", json={"role": "instructor"})

        with autotest.step("Assert: 200, role=instructor в ответе"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_equal(body["id"], "u1", "id=u1")
            assert_equal(body["role"], "instructor", "role=instructor")

    @autotest.num("1821")
    @autotest.external_id("7cdfa3fa-21e3-4c79-a6ba-710cef3113c4")
    @autotest.name("PATCH /admin/users/{id}: смена собственной роли — 400")
    async def test_7cdfa3fa_patch_own_role_rejected(self):
        with autotest.step("Act: admin-001 пытается сменить свою роль"):
            async with self._client() as client:
                resp = await client.patch("/admin/users/admin-001", json={"role": "student"})

        with autotest.step("Assert: 400"):
            assert_equal(resp.status_code, 400, "status 400")
            assert_in("detail", resp.json(), "detail в ответе")

    @autotest.num("1822")
    @autotest.external_id("e3556b2c-9572-4579-8104-59a7b7645966")
    @autotest.name("PATCH /admin/users/{id}: смена флагов на себе — разрешено")
    async def test_e3556b2c_patch_flags_on_self_allowed(self):
        with autotest.step("Act: admin-001 ставит can_select_model=true себе"):
            async with self._client() as client:
                resp = await client.patch(
                    "/admin/users/admin-001",
                    json={"can_select_model": True},
                )

        with autotest.step("Assert: 200, can_select_model=true"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_equal(resp.json()["can_select_model"], True, "can_select_model=True")

    @autotest.num("1823")
    @autotest.external_id("4ad6d8f1-3de4-4290-8085-d458057b9f12")
    @autotest.name("GET /admin/users: не-admin получает 403")
    async def test_4ad6d8f1_non_admin_gets_403(self):
        with autotest.step("Act: student запрашивает /admin/users"):
            async with self._student_client() as client:
                resp = await client.get("/admin/users")

        with autotest.step("Assert: 403"):
            assert_equal(resp.status_code, 403, "status 403")


class TestAdminDataEndpoints:
    """HTTP tests for GET /admin/data/{table}."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(MCPAudit.__table__.create)

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

    async def _seed_audit_rows(self, rows: list[MCPAudit]) -> None:
        async with self.session_factory() as db:
            db.add_all(rows)
            await db.commit()

    @autotest.num("1927")
    @autotest.external_id("00bc7af4-e5d0-42bb-b16a-46244508c1e9")
    @autotest.name("GET /admin/data/{table}: не-admin получает 403")
    async def test_00bc7af4_non_admin_403(self):
        with autotest.step("Act: student запрашивает /admin/data/mcp_audit"):
            async with self._student_client() as client:
                resp = await client.get("/admin/data/mcp_audit")

        with autotest.step("Assert: 403"):
            assert_equal(resp.status_code, 403, "status 403")

    @autotest.num("1928")
    @autotest.external_id("1284e471-a594-4ab6-9d47-7bd58895e24e")
    @autotest.name("GET /admin/data/{table}: неизвестная таблица → 404")
    async def test_1284e471_unknown_table_404(self):
        with autotest.step("Act: запросить несуществующую таблицу"):
            async with self._client() as client:
                resp = await client.get("/admin/data/not_a_table")

        with autotest.step("Assert: 404, detail=Unknown table"):
            assert_equal(resp.status_code, 404, "status 404")
            assert_equal(resp.json()["detail"], "Unknown table", "detail")

    @autotest.num("1929")
    @autotest.external_id("d797ce5c-1aca-41f5-9862-d693b3d0bd05")
    @autotest.name("GET /admin/data/mcp_audit: пагинация и total")
    async def test_d797ce5c_pagination_and_total(self):
        now = datetime.datetime.now(datetime.UTC)
        rows = [
            MCPAudit(
                id=str(uuid.uuid4()),
                user_id="u1",
                session_id="s1",
                tool="ping",
                kind="observe",
                ts=now,
                success=True,
            ),
            MCPAudit(
                id=str(uuid.uuid4()),
                user_id="u2",
                session_id="s2",
                tool="pong",
                kind="act",
                ts=now,
                success=False,
            ),
        ]
        await self._seed_audit_rows(rows)

        with autotest.step("Act: page_size=1, page=1"):
            async with self._client() as client:
                resp = await client.get("/admin/data/mcp_audit?page=1&page_size=1")

        with autotest.step("Assert: 200, total=2, items=1, columns совпадают со spec"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_equal(body["total"], 2, "total=2")
            assert_equal(len(body["items"]), 1, "items len=1")
            assert_equal(body["page"], 1, "page=1")
            assert_equal(body["page_size"], 1, "page_size=1")
            spec_cols = ADMIN_TABLES["mcp_audit"].columns
            assert_equal(body["columns"], spec_cols, "columns == spec.columns")

    @autotest.num("1930")
    @autotest.external_id("103b8e07-0ab4-467c-b6e7-f0f8c1b8869f")
    @autotest.name("GET /admin/data/mcp_audit: search сужает результаты")
    async def test_103b8e07_search_narrows(self):
        now = datetime.datetime.now(datetime.UTC)
        rows = [
            MCPAudit(
                id=str(uuid.uuid4()),
                user_id="u1",
                session_id="s1",
                tool="gns3.list_nodes",
                kind="observe",
                ts=now,
                success=True,
            ),
            MCPAudit(
                id=str(uuid.uuid4()),
                user_id="u2",
                session_id="s2",
                tool="docker.run",
                kind="act",
                ts=now,
                success=True,
            ),
        ]
        await self._seed_audit_rows(rows)

        with autotest.step("Act: search=gns3"):
            async with self._client() as client:
                resp = await client.get("/admin/data/mcp_audit?search=gns3")

        with autotest.step("Assert: возвращает только строку с gns3"):
            assert_equal(resp.status_code, 200, "status 200")
            body = resp.json()
            assert_equal(body["total"], 1, "total=1 после поиска")
            assert_true("gns3" in body["items"][0]["tool"], "tool содержит gns3")

    @autotest.num("1931")
    @autotest.external_id("d998c922-fc26-4596-b3a3-627797bd7ff7")
    @autotest.name("GET /admin/data/mcp_audit: сортировка asc vs desc по ts")
    async def test_d998c922_sort_asc_vs_desc(self):
        t1 = datetime.datetime(2025, 1, 1, tzinfo=datetime.UTC)
        t2 = datetime.datetime(2025, 6, 1, tzinfo=datetime.UTC)
        rows = [
            MCPAudit(
                id=str(uuid.uuid4()),
                user_id="u1",
                session_id="s1",
                tool="a",
                kind="observe",
                ts=t1,
                success=True,
            ),
            MCPAudit(
                id=str(uuid.uuid4()),
                user_id="u2",
                session_id="s2",
                tool="b",
                kind="observe",
                ts=t2,
                success=True,
            ),
        ]
        await self._seed_audit_rows(rows)

        with autotest.step("Act: order=asc"):
            async with self._client() as client:
                resp_asc = await client.get("/admin/data/mcp_audit?sort=ts&order=asc")

        with autotest.step("Act: order=desc"):
            async with self._client() as client:
                resp_desc = await client.get("/admin/data/mcp_audit?sort=ts&order=desc")

        with autotest.step("Assert: asc первый ts < desc первый ts"):
            assert_equal(resp_asc.status_code, 200, "asc 200")
            assert_equal(resp_desc.status_code, 200, "desc 200")
            first_asc = resp_asc.json()["items"][0]["ts"]
            first_desc = resp_desc.json()["items"][0]["ts"]
            assert_true(first_asc < first_desc, "asc первый раньше desc первого")
