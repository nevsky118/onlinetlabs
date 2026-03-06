# E2E: полный рабочий цикл GNS3 через ApiClient.

import uuid

import httpx
import pytest

from src.api_client import GNS3ApiClient
from tests.report import autotests

pytestmark = [pytest.mark.e2e]


@pytest.fixture
async def e2e_project(api_client: GNS3ApiClient):
    """Создаёт проект, отдаёт, удаляет после теста."""
    project_name = f"e2e-test-{uuid.uuid4().hex[:8]}"
    project = await api_client._request(
        "POST", "/v3/projects", json={"name": project_name},
    )
    project_id = project["project_id"]
    yield project_id
    # cleanup
    try:
        await api_client._request("DELETE", f"/v3/projects/{project_id}")
    except Exception:
        pass


class TestE2EFullWorkflow:
    """Полный workflow: project -> nodes -> link -> delete."""

    @autotests.num("380")
    @autotests.external_id("f0a1b2c3-d4e5-4f67-8901-abcdef380000")
    @autotests.name("GNS3 e2e: полный цикл — создание нод, линк, удаление")
    async def test_full_workflow(self, api_client: GNS3ApiClient, e2e_project: str):
        pid = e2e_project

        with autotests.step("Получаем список шаблонов"):
            templates = await api_client.list_templates()
            vpcs_tpl = next(
                (template for template in templates if template.get("template_type") == "vpcs"),
                None,
            )
            assert vpcs_tpl is not None, "VPCS template not found"
            tpl_id = vpcs_tpl["template_id"]

        with autotests.step("Создаём две ноды"):
            node1 = await api_client.create_node_from_template(pid, tpl_id, x=0, y=0)
            node2 = await api_client.create_node_from_template(pid, tpl_id, x=100, y=0)
            assert node1["node_id"]
            assert node2["node_id"]

        with autotests.step("Проверяем список нод"):
            nodes = await api_client.list_nodes(pid)
            node_ids = [node["node_id"] for node in nodes]
            assert node1["node_id"] in node_ids
            assert node2["node_id"] in node_ids

        with autotests.step("Создаём линк между нодами"):
            link = await api_client.create_link(
                pid,
                [
                    {
                        "node_id": node1["node_id"],
                        "adapter_number": 0,
                        "port_number": 0,
                    },
                    {
                        "node_id": node2["node_id"],
                        "adapter_number": 0,
                        "port_number": 0,
                    },
                ],
            )
            assert link["link_id"]

        with autotests.step("Проверяем список линков"):
            links = await api_client.list_links(pid)
            assert any(lnk["link_id"] == link["link_id"] for lnk in links)

        with autotests.step("Удаляем линк"):
            await api_client.delete_link(pid, link["link_id"])
            links = await api_client.list_links(pid)
            link_ids = [lnk["link_id"] for lnk in links]
            assert link["link_id"] not in link_ids


class TestE2EBasic:
    """Базовые проверки доступности GNS3."""

    @autotests.num("381")
    @autotests.external_id("f0a1b2c3-d4e5-4f67-8901-abcdef381000")
    @autotests.name("GNS3 e2e: версия доступна")
    async def test_version_available(self, api_client: GNS3ApiClient):
        with autotests.step("Запрашиваем версию"):
            version = await api_client.get_version()
        with autotests.step("Проверяем ответ"):
            assert "version" in version
            assert isinstance(version["version"], str)

    @autotests.num("382")
    @autotests.external_id("f0a1b2c3-d4e5-4f67-8901-abcdef382000")
    @autotests.name("GNS3 e2e: список шаблонов")
    async def test_list_templates(self, api_client: GNS3ApiClient):
        with autotests.step("Запрашиваем шаблоны"):
            templates = await api_client.list_templates()
        with autotests.step("Проверяем наличие шаблонов"):
            assert isinstance(templates, list)
            assert len(templates) > 0, "No templates available"


class TestE2EStudentIsolation:
    """Проверка per-student изоляции через ACL."""

    @autotests.num("383")
    @autotests.external_id("f0a1b2c3-d4e5-4f67-8901-abcdef383000")
    @autotests.name("GNS3 e2e: создание студента с JWT")
    async def test_student_auth(self, api_client: GNS3ApiClient, gns3_url: str):
        username = f"test-student-{uuid.uuid4().hex[:8]}"
        password = "testpass123"

        with autotests.step("Создаём студента через admin API"):
            student = await api_client._request(
                "POST", "/v3/access/users",
                json={"username": username, "password": password},
            )
            student_id = student["user_id"]

        try:
            with autotests.step("Получаем JWT для студента"):
                token_resp = await api_client._request(
                    "POST", "/v3/access/users/authenticate",
                    json={"username": username, "password": password},
                )
                student_token = token_resp["access_token"]

            with autotests.step("Студент может обращаться к API"):
                async with httpx.AsyncClient(
                    base_url=gns3_url,
                    headers={"Authorization": f"Bearer {student_token}"},
                ) as student_client:
                    student_api_client = GNS3ApiClient(student_client)
                    version = await student_api_client.get_version()
                    assert "version" in version
        finally:
            with autotests.step("Удаляем студента"):
                await api_client._request("DELETE", f"/v3/access/users/{student_id}")
