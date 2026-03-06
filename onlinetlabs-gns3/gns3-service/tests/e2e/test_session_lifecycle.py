# E2E: полный жизненный цикл сессии.

import uuid

import httpx
import pytest

from tests.report import autotests

pytestmark = [pytest.mark.e2e]


class TestSessionLifecycle:
    @autotests.num("470")
    @autotests.external_id("a1b2c3d4-0001-4aaa-bbbb-470000000001")
    @autotests.name("GNS3 Service e2e: create + verify + delete сессию")
    async def test_full_lifecycle(self, admin_client, db_session, setup_db):
        from src.service import SessionService

        with autotests.step("Подготовка — нужен template project"):
            response = await admin_client._client.post(
                "/v3/projects", json={"name": "e2e-template"}
            )
            template = response.json()
            template_pid = template["project_id"]

        try:
            with autotests.step("Создаём сессию"):
                svc = SessionService(
                    admin_client=admin_client, gns3_url="http://localhost:3080"
                )
                user_id = uuid.uuid4().hex[:16]
                result = await svc.create_session(
                    db=db_session,
                    user_id=user_id,
                    template_project_id=template_pid,
                )
                assert result.gns3_jwt
                assert result.gns3_username.startswith("student-")
                assert result.gns3_password

            with autotests.step("Студент может залогиниться"):
                async with httpx.AsyncClient(
                    base_url="http://localhost:3080"
                ) as client:
                    response = await client.post(
                        "/v3/access/users/authenticate",
                        json={
                            "username": result.gns3_username,
                            "password": result.gns3_password,
                        },
                    )
                    assert response.status_code == 200
                    assert response.json()["access_token"]

            with autotests.step("Удаляем сессию"):
                await svc.delete_session(
                    db=db_session, session_id=result.session_id
                )

            with autotests.step("Студент больше не может залогиниться"):
                async with httpx.AsyncClient(
                    base_url="http://localhost:3080"
                ) as client:
                    response = await client.post(
                        "/v3/access/users/authenticate",
                        json={
                            "username": result.gns3_username,
                            "password": result.gns3_password,
                        },
                    )
                    assert response.status_code != 200
        finally:
            with autotests.step("Cleanup template"):
                await admin_client._client.delete(
                    f"/v3/projects/{template_pid}"
                )
