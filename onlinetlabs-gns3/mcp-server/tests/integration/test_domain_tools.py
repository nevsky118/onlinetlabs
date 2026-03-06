import pytest

from tests.helpers.factories import build_session_context
from tests.helpers.fakes import FakeGNS3ApiClient
from tests.report import autotests

from onlinetlabs_mcp_sdk.server import OnlinetlabsMCPServer

from src.server import GNS3Server
from src.domain_tools import register_domain_tools
from src.log_buffer import LogBuffer

pytestmark = [pytest.mark.integration, pytest.mark.domain_tools]

VALID_CTX = {
    "user_id": "test-student",
    "session_id": "test-session",
    "environment_url": "http://localhost:3080",
    "project_id": "test-project-id",
    "metadata": {"gns3_jwt": "test-jwt-token"},
}


@pytest.fixture
def fake_client():
    return FakeGNS3ApiClient()


@pytest.fixture
def mcp_server(fake_client):
    from onlinetlabs_mcp_sdk.models import LogLevel
    buf = LogBuffer()
    buf._add_entry(LogLevel.ERROR, "test error")
    impl = GNS3Server(api_client=fake_client, log_buffer=buf)
    server = OnlinetlabsMCPServer("gns3-test", impl)

    async def get_client(ctx):
        return fake_client

    def get_project_id(ctx):
        return ctx.project_id

    register_domain_tools(server, get_client, get_project_id)
    return server


def _get_tool_fn(server, name):
    return server.mcp._tool_manager._tools[name].fn


class TestDomainToolsRegistration:
    @autotests.num("370")
    @autotests.external_id("d1e2f3a4-0001-4ddd-eeee-000000000001")
    @autotests.name("GNS3 Domain Tools: все 25 инструментов зарегистрированы")
    def test_all_tools_registered(self, mcp_server):
        with autotests.step("Проверяем количество domain tools"):
            expected_domain = {
                "start_node", "stop_node", "reload_node", "suspend_node",
                "isolate_node", "unisolate_node", "start_all_nodes", "stop_all_nodes",
                "create_link", "delete_link", "start_capture", "stop_capture", "set_link_filter",
                "get_console_info", "reset_console",
                "list_templates", "create_node_from_template",
                "open_project", "close_project", "lock_project", "unlock_project", "duplicate_project",
                "list_snapshots", "create_snapshot", "restore_snapshot",
            }
            tool_names = set(mcp_server.tool_names)
            assert expected_domain.issubset(tool_names), f"Missing: {expected_domain - tool_names}"


class TestDomainToolsExecution:
    @autotests.num("371")
    @autotests.external_id("d1e2f3a4-0002-4ddd-eeee-000000000002")
    @autotests.name("GNS3 Domain Tools: start_node")
    async def test_start_node(self, mcp_server):
        fn = _get_tool_fn(mcp_server, "start_node")
        with autotests.step("Вызываем start_node"):
            result = await fn(ctx=VALID_CTX, node_id="n1")
        with autotests.step("Проверяем успех"):
            assert result["success"] is True

    @autotests.num("372")
    @autotests.external_id("d1e2f3a4-0003-4ddd-eeee-000000000003")
    @autotests.name("GNS3 Domain Tools: create_link")
    async def test_create_link(self, mcp_server):
        fn = _get_tool_fn(mcp_server, "create_link")
        nodes = [
            {"node_id": "n1", "adapter_number": 0, "port_number": 0},
            {"node_id": "n2", "adapter_number": 0, "port_number": 0},
        ]
        with autotests.step("Создаём линк"):
            result = await fn(ctx=VALID_CTX, nodes=nodes)
        with autotests.step("Проверяем успех"):
            assert result["success"] is True

    @autotests.num("373")
    @autotests.external_id("d1e2f3a4-0004-4ddd-eeee-000000000004")
    @autotests.name("GNS3 Domain Tools: get_console_info")
    async def test_get_console_info(self, mcp_server):
        fn = _get_tool_fn(mcp_server, "get_console_info")
        with autotests.step("Получаем console info"):
            result = await fn(ctx=VALID_CTX, node_id="n1")
        with autotests.step("Проверяем console данные"):
            assert result["console"] == 5000
            assert result["console_type"] == "telnet"

    @autotests.num("374")
    @autotests.external_id("d1e2f3a4-0005-4ddd-eeee-000000000005")
    @autotests.name("GNS3 Domain Tools: list_templates")
    async def test_list_templates(self, mcp_server):
        fn = _get_tool_fn(mcp_server, "list_templates")
        with autotests.step("Получаем шаблоны"):
            result = await fn(ctx=VALID_CTX)
        with autotests.step("Проверяем результат"):
            assert len(result) == 1
            assert result[0]["name"] == "VPCS"

    @autotests.num("375")
    @autotests.external_id("d1e2f3a4-0006-4ddd-eeee-000000000006")
    @autotests.name("GNS3 Domain Tools: create_snapshot")
    async def test_create_snapshot(self, mcp_server):
        fn = _get_tool_fn(mcp_server, "create_snapshot")
        with autotests.step("Создаём снапшот"):
            result = await fn(ctx=VALID_CTX, name="checkpoint1")
        with autotests.step("Проверяем успех"):
            assert result["success"] is True

    @autotests.num("376")
    @autotests.external_id("d1e2f3a4-0007-4ddd-eeee-000000000007")
    @autotests.name("GNS3 Domain Tools: start_all_nodes")
    async def test_start_all_nodes(self, mcp_server):
        fn = _get_tool_fn(mcp_server, "start_all_nodes")
        with autotests.step("Запускаем все ноды"):
            result = await fn(ctx=VALID_CTX)
        with autotests.step("Проверяем успех"):
            assert result["success"] is True
