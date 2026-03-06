# E2E: детальные проверки сессий — ACL, cleanup, дубликация, роли.

import uuid

import httpx
import pytest

from tests.report import autotests

pytestmark = [pytest.mark.e2e]

GNS3_URL = "http://localhost:3080"


class TestDuplicateProjectNaming:
    """Проверка что дубликат проекта получает корректное имя."""

    @autotests.num("471")
    @autotests.external_id("a1b2c3d4-0002-4aaa-bbbb-471000000001")
    @autotests.name("GNS3 Service e2e: дубликат проекта содержит имя сессии")
    async def test_duplicate_has_session_name(self, admin_client, session_result):
        with autotests.step("Проверяем имя дублированного проекта"):
            response = await admin_client._client.get(
                f"/v3/projects/{session_result.project_id}"
            )
            assert response.status_code == 200
            project = response.json()
            assert project["name"].startswith("session-student-")


class TestRoleAndACLChain:
    """Проверка что ACE привязывает студента к проекту через builtin User role."""

    @autotests.num("472")
    @autotests.external_id("a1b2c3d4-0003-4aaa-bbbb-472000000001")
    @autotests.name("GNS3 Service e2e: ACE создан для студента с ролью User")
    async def test_ace_created_with_user_role(self, admin_client, session_result):
        with autotests.step("Находим builtin User role"):
            response = await admin_client._client.get("/v3/access/roles")
            roles = response.json()
            user_role = next(
                (role for role in roles if role["name"] == "User" and role["is_builtin"]),
                None,
            )
            assert user_role is not None, "Built-in User role not found"

        with autotests.step("Проверяем ACE для студента + User role + проект"):
            response = await admin_client._client.get("/v3/access/acl")
            acl_entries = response.json()
            matching = [
                ace for ace in acl_entries
                if ace["user_id"] == session_result.gns3_user_id
                and ace["role_id"] == user_role["role_id"]
                and f"/projects/{session_result.project_id}" in ace["path"]
            ]
            assert len(matching) == 1, "ACE not found for student + User role + project"


class TestSessionCleanup:
    """Проверка что delete_session реально чистит ресурсы в GNS3."""

    @autotests.num("473")
    @autotests.external_id("a1b2c3d4-0004-4aaa-bbbb-473000000001")
    @autotests.name("GNS3 Service e2e: после удаления сессии пользователь удалён из GNS3")
    async def test_cleanup_removes_gns3_user(
        self, admin_client, db_session, setup_db, template_project,
    ):
        from src.service import SessionService

        with autotests.step("Создаём сессию"):
            svc = SessionService(admin_client=admin_client, gns3_url=GNS3_URL)
            user_id = uuid.uuid4().hex[:16]
            result = await svc.create_session(
                db=db_session, user_id=user_id,
                template_project_id=template_project,
            )
            gns3_user_id = result.gns3_user_id
            gns3_username = result.gns3_username
            gns3_password = result.gns3_password

        with autotests.step("Подтверждаем что пользователь существует"):
            response = await admin_client._client.get(
                f"/v3/access/users/{gns3_user_id}"
            )
            assert response.status_code == 200

        with autotests.step("Удаляем сессию"):
            await svc.delete_session(db=db_session, session_id=result.session_id)

        with autotests.step("Пользователь больше не существует в GNS3"):
            response = await admin_client._client.get(
                f"/v3/access/users/{gns3_user_id}"
            )
            assert response.status_code == 404

        with autotests.step("Аутентификация невозможна"):
            async with httpx.AsyncClient(base_url=GNS3_URL) as client:
                response = await client.post(
                    "/v3/access/users/authenticate",
                    json={"username": gns3_username, "password": gns3_password},
                )
                assert response.status_code != 200

        # cleanup project left behind
        try:
            await admin_client._client.delete(
                f"/v3/projects/{result.project_id}"
            )
        except Exception:
            pass


class TestACLIsolation:
    """Проверка per-student изоляции проектов через ACL.

    GNS3 v3: GET /v3/projects не возвращает ACE-scoped проекты в listing,
    но прямой доступ GET /v3/projects/{id} работает корректно.
    Тест проверяет изоляцию через прямой доступ к проектам.
    """

    @autotests.num("474")
    @autotests.external_id("a1b2c3d4-0005-4aaa-bbbb-474000000001")
    @autotests.name("GNS3 Service e2e: студент имеет доступ только к своему проекту")
    async def test_student_sees_only_own_project(
        self, admin_client, db_session, setup_db, template_project,
    ):
        from src.service import SessionService

        svc = SessionService(admin_client=admin_client, gns3_url=GNS3_URL)
        results = []

        with autotests.step("Создаём две сессии для разных студентов"):
            for _ in range(2):
                user_id = uuid.uuid4().hex[:16]
                result = await svc.create_session(
                    db=db_session, user_id=user_id,
                    template_project_id=template_project,
                )
                results.append(result)

        try:
            with autotests.step("Студент 1 может получить свой проект напрямую"):
                async with httpx.AsyncClient(
                    base_url=GNS3_URL,
                    headers={"Authorization": f"Bearer {results[0].gns3_jwt}"},
                ) as client:
                    response = await client.get(f"/v3/projects/{results[0].project_id}")
                    assert response.status_code == 200

            with autotests.step("Студент 1 НЕ может получить проект студента 2"):
                async with httpx.AsyncClient(
                    base_url=GNS3_URL,
                    headers={"Authorization": f"Bearer {results[0].gns3_jwt}"},
                ) as client:
                    response = await client.get(f"/v3/projects/{results[1].project_id}")
                    assert response.status_code in (403, 404), f"Expected 403/404, got {response.status_code}"

            with autotests.step("Студент 2 может получить свой проект напрямую"):
                async with httpx.AsyncClient(
                    base_url=GNS3_URL,
                    headers={"Authorization": f"Bearer {results[1].gns3_jwt}"},
                ) as client:
                    response = await client.get(f"/v3/projects/{results[1].project_id}")
                    assert response.status_code == 200

            with autotests.step("Студент 2 НЕ может получить проект студента 1"):
                async with httpx.AsyncClient(
                    base_url=GNS3_URL,
                    headers={"Authorization": f"Bearer {results[1].gns3_jwt}"},
                ) as client:
                    response = await client.get(f"/v3/projects/{results[0].project_id}")
                    assert response.status_code in (403, 404), f"Expected 403/404, got {response.status_code}"
        finally:
            with autotests.step("Cleanup обеих сессий"):
                for result in results:
                    try:
                        await svc.delete_session(
                            db=db_session, session_id=result.session_id,
                        )
                    except Exception:
                        pass
                    for cleanup in [
                        lambda res=result: admin_client._client.delete(
                            f"/v3/projects/{res.project_id}"
                        ),
                        lambda res=result: admin_client._client.delete(
                            f"/v3/access/users/{res.gns3_user_id}"
                        ),
                    ]:
                        try:
                            await cleanup()
                        except Exception:
                            pass


class TestStaleResourceResilience:
    """Проверка что повторное создание сессии не ломается на stale данных."""

    @autotests.num("475")
    @autotests.external_id("a1b2c3d4-0006-4aaa-bbbb-475000000001")
    @autotests.name("GNS3 Service e2e: две сессии для разных user_id создаются без конфликтов")
    async def test_two_sessions_no_conflict(
        self, admin_client, db_session, setup_db, template_project,
    ):
        from src.service import SessionService

        svc = SessionService(admin_client=admin_client, gns3_url=GNS3_URL)
        results = []

        with autotests.step("Создаём первую сессию"):
            result1 = await svc.create_session(
                db=db_session, user_id=uuid.uuid4().hex[:16],
                template_project_id=template_project,
            )
            results.append(result1)

        with autotests.step("Создаём вторую сессию"):
            result2 = await svc.create_session(
                db=db_session, user_id=uuid.uuid4().hex[:16],
                template_project_id=template_project,
            )
            results.append(result2)

        try:
            with autotests.step("Обе сессии имеют разные project_id"):
                assert result1.project_id != result2.project_id

            with autotests.step("Обе сессии имеют разных пользователей"):
                assert result1.gns3_username != result2.gns3_username
                assert result1.gns3_user_id != result2.gns3_user_id

            with autotests.step("Оба JWT валидны"):
                for result in results:
                    async with httpx.AsyncClient(
                        base_url=GNS3_URL,
                        headers={"Authorization": f"Bearer {result.gns3_jwt}"},
                    ) as client:
                        response = await client.get("/v3/version")
                        assert response.status_code == 200
        finally:
            with autotests.step("Cleanup"):
                for result in results:
                    try:
                        await svc.delete_session(
                            db=db_session, session_id=result.session_id,
                        )
                    except Exception:
                        pass
                    for cleanup in [
                        lambda res=result: admin_client._client.delete(
                            f"/v3/projects/{res.project_id}"
                        ),
                        lambda res=result: admin_client._client.delete(
                            f"/v3/access/users/{res.gns3_user_id}"
                        ),
                    ]:
                        try:
                            await cleanup()
                        except Exception:
                            pass


class TestStudentProjectAccess:
    """Проверка что студент может работать с нодами в своём проекте."""

    @autotests.num("476")
    @autotests.external_id("a1b2c3d4-0007-4aaa-bbbb-476000000001")
    @autotests.name("GNS3 Service e2e: студент может создать ноду в своём проекте")
    async def test_student_can_create_node(self, admin_client, session_result):
        with autotests.step("Получаем VPCS template"):
            async with httpx.AsyncClient(
                base_url=GNS3_URL,
                headers={"Authorization": f"Bearer {session_result.gns3_jwt}"},
            ) as client:
                response = await client.get("/v3/templates")
                templates = response.json()
                vpcs = next(
                    (template for template in templates if template.get("template_type") == "vpcs"),
                    None,
                )
                assert vpcs is not None, "VPCS template not found"

        with autotests.step("Студент создаёт VPCS ноду в своём проекте"):
            async with httpx.AsyncClient(
                base_url=GNS3_URL,
                headers={"Authorization": f"Bearer {session_result.gns3_jwt}"},
            ) as client:
                response = await client.post(
                    f"/v3/projects/{session_result.project_id}"
                    f"/templates/{vpcs['template_id']}",
                    json={"x": 0, "y": 0},
                )
                assert response.status_code in (200, 201), f"Got {response.status_code}: {response.text}"
                node = response.json()
                assert node["node_id"]

        with autotests.step("Нода видна в списке нод проекта"):
            async with httpx.AsyncClient(
                base_url=GNS3_URL,
                headers={"Authorization": f"Bearer {session_result.gns3_jwt}"},
            ) as client:
                response = await client.get(
                    f"/v3/projects/{session_result.project_id}/nodes"
                )
                nodes = response.json()
                assert any(nd["node_id"] == node["node_id"] for nd in nodes)
