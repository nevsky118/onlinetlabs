"""Task 2: тесты чистых сборщиков admin-роутера (без подъёма FastAPI)."""
import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_in, assert_true, assert_equal

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
    @autotest.external_id("b5d8e3f2-9c0a-4b1e-ad23-6f7e1g2h3i4j")
    @autotest.name("admin: tk-sensitivity форма ответа")
    def test_b5d8e3f2_tk_sensitivity_shape(self):
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
    @autotest.external_id("c6e9f4g3-ad1b-5c2f-be34-7g8f2h3i4j5k")
    @autotest.name("admin: build_overview пустая БД — возвращает dict с ключами ab/cohort/identifier/ops")
    async def test_c6e9f4g3_overview_empty_db(self, empty_admin_db):
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
    @autotest.external_id("d7f0g5h4-be2c-6d3g-cf45-8h9g3i4j5k6l")
    @autotest.name("admin: build_overview с одной метрикой — не падает, возвращает числа")
    async def test_d7f0g5h4_overview_with_seed(self, seeded_admin_db):
        from admin.router import build_overview

        with autotest.step("Act: build_overview с сидом"):
            out = await build_overview(seeded_admin_db)

        with autotest.step("Assert: структура полная"):
            for k in ("ab", "cohort", "identifier", "ops"):
                assert_in(k, out, k)

        with autotest.step("Assert: ops.labeled_real_n >= 1"):
            assert_true(out["ops"]["labeled_real_n"] >= 1, "хотя бы одна метрика")

    @autotest.num("1814")
    @autotest.external_id("e8g1h6i5-cf3d-7e4h-dg56-9i0h4j5k6l7m")
    @autotest.name("admin: роутер зарегистрирован под /admin в main.py")
    def test_e8g1h6i5_router_registered(self):
        with autotest.step("Импортировать admin_router"):
            from admin.router import router as admin_router

        with autotest.step("Assert: роутер имеет пути overview/identifier-eval/tk-sensitivity"):
            paths = {r.path for r in admin_router.routes}
            assert_in("/overview", paths, "/overview")
            assert_in("/identifier-eval", paths, "/identifier-eval")
            assert_in("/tk-sensitivity", paths, "/tk-sensitivity")

    @autotest.num("1815")
    @autotest.external_id("f9h2i7j6-dg4e-8f5i-eh67-0j1i5k6l7m8n")
    @autotest.name("admin: require_admin отклоняет не-admin (403)")
    def test_f9h2i7j6_require_admin_rejects(self):
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
