from unittest.mock import AsyncMock

import pytest
from mcp_sdk.context import SessionContext
from mcp_sdk.testing import autotest

from src.domain_tools import register_domain_tools

pytestmark = [pytest.mark.unit, pytest.mark.domain_tools]

GNS3_URL = "http://gns3-test:3080"
PROJECT_ID = "proj-1"
NODE_ID = "node-1"
LINK_ID = "link-1"
TEMPLATE_ID = "tpl-1"
SNAPSHOT_ID = "snap-1"


class StubServer:
    """Минимальная замена OnlinetlabsMCPServer для перехвата зарегистрированных tool-функций."""

    def __init__(self) -> None:
        self.tools: dict[str, callable] = {}
        self.descriptions: dict[str, str] = {}

    def domain_tool(self, **kwargs):
        description = kwargs.get("description", "")

        def wrapper(fn):
            self.tools[fn.__name__] = fn
            self.descriptions[fn.__name__] = description
            return fn

        return wrapper


def _make_ctx_dict(**overrides) -> dict:
    defaults = dict(
        user_id="u1",
        session_id="s1",
        environment_url=GNS3_URL,
        project_id=PROJECT_ID,
    )
    return defaults | overrides


@pytest.fixture()
def registered():
    """Регистрирует domain tools на stub-сервере и возвращает (server, api_mock)."""
    server = StubServer()
    api = AsyncMock()

    async def get_client(session: SessionContext):
        return api

    def get_project_id(session: SessionContext) -> str:
        return session.project_id

    register_domain_tools(server, get_client, get_project_id)
    return server, api


EXPECTED_TOOL_NAMES = {
    # node lifecycle
    "start_node",
    "stop_node",
    "reload_node",
    "suspend_node",
    "isolate_node",
    "unisolate_node",
    "start_all_nodes",
    "stop_all_nodes",
    # links
    "create_link",
    "delete_link",
    "start_capture",
    "stop_capture",
    "set_link_filter",
    # console
    "get_console_info",
    "reset_console",
    # templates
    "list_templates",
    "create_node_from_template",
    # project ops
    "open_project",
    "close_project",
    "lock_project",
    "unlock_project",
    "duplicate_project",
    # snapshots
    "list_snapshots",
    "create_snapshot",
    "restore_snapshot",
    # console/exec (наблюдение состояния устройства через MCP)
    "exec_vtysh",
}


class TestRegistration:
    @autotest.num("810")
    @autotest.external_id("gns3-domain-tools-registered")
    @autotest.name("register_domain_tools: регистрирует полный набор GNS3 инструментов")
    def test_all_expected_tools_registered(self, registered):
        with autotest.step("Получаем зарегистрированные имена"):
            server, _ = registered
            registered_names = set(server.tools.keys())

        with autotest.step("Проверяем, что ожидаемые tools присутствуют"):
            assert EXPECTED_TOOL_NAMES.issubset(registered_names), (
                f"missing: {EXPECTED_TOOL_NAMES - registered_names}"
            )

    @autotest.num("811")
    @autotest.external_id("gns3-domain-tools-descriptions-non-empty")
    @autotest.name("register_domain_tools: каждый tool имеет непустое description")
    def test_each_tool_has_description(self, registered):
        with autotest.step("Берём описания"):
            server, _ = registered

        with autotest.step("Все описания непустые"):
            for name in EXPECTED_TOOL_NAMES:
                assert server.descriptions[name], f"tool {name} has empty description"


class TestDispatch:
    @autotest.num("812")
    @autotest.external_id("gns3-domain-tools-dispatch-start-node")
    @autotest.name("start_node: вызывает api_client.start_node с project_id и node_id")
    async def test_start_node_dispatch(self, registered):
        with autotest.step("Готовим api mock"):
            server, api = registered
            api.start_node.return_value = {"status": "started"}

        with autotest.step("Вызываем start_node"):
            result = await server.tools["start_node"](_make_ctx_dict(), node_id=NODE_ID)

        with autotest.step("Проверяем диспатч и формат ответа"):
            api.start_node.assert_awaited_once_with(PROJECT_ID, NODE_ID)
            assert result["success"] is True
            assert NODE_ID in result["message"]
            assert result["data"] == {"status": "started"}

    @autotest.num("813")
    @autotest.external_id("gns3-domain-tools-dispatch-isolate-node")
    @autotest.name("isolate_node: вызывает api_client.isolate_node")
    async def test_isolate_node_dispatch(self, registered):
        with autotest.step("Готовим api mock"):
            server, api = registered
            api.isolate_node.return_value = {"isolated_links": ["l1", "l2"]}

        with autotest.step("Вызываем isolate_node"):
            result = await server.tools["isolate_node"](_make_ctx_dict(), node_id=NODE_ID)

        with autotest.step("Проверяем дипатч и payload"):
            api.isolate_node.assert_awaited_once_with(PROJECT_ID, NODE_ID)
            assert result["success"] is True
            assert "isolated" in result["message"]
            assert result["data"] == {"isolated_links": ["l1", "l2"]}

    @autotest.num("814")
    @autotest.external_id("gns3-domain-tools-dispatch-get-console-info")
    @autotest.name("get_console_info: возвращает console-поля ноды без флага success")
    async def test_get_console_info_returns_node_fields(self, registered):
        with autotest.step("Готовим api mock"):
            server, api = registered
            api.get_node.return_value = {
                "console": 5000,
                "console_type": "telnet",
                "console_host": "127.0.0.1",
            }

        with autotest.step("Вызываем get_console_info"):
            result = await server.tools["get_console_info"](_make_ctx_dict(), NODE_ID)

        with autotest.step("Проверяем форму ответа"):
            api.get_node.assert_awaited_once_with(PROJECT_ID, NODE_ID)
            assert result == {
                "node_id": NODE_ID,
                "console": 5000,
                "console_type": "telnet",
                "console_host": "127.0.0.1",
            }

    @autotest.num("815")
    @autotest.external_id("gns3-domain-tools-dispatch-delete-link")
    @autotest.name("delete_link: вызывает api_client.delete_link, success=True")
    async def test_delete_link_dispatch(self, registered):
        with autotest.step("Готовим api mock"):
            server, api = registered
            api.delete_link.return_value = None

        with autotest.step("Вызываем delete_link"):
            result = await server.tools["delete_link"](_make_ctx_dict(), link_id=LINK_ID)

        with autotest.step("Проверяем"):
            api.delete_link.assert_awaited_once_with(PROJECT_ID, LINK_ID)
            assert result["success"] is True
            assert LINK_ID in result["message"]

    @autotest.num("816")
    @autotest.external_id("gns3-domain-tools-dispatch-create-snapshot")
    @autotest.name("create_snapshot: проксирует имя в api_client.create_snapshot")
    async def test_create_snapshot_dispatch(self, registered):
        with autotest.step("Готовим api mock"):
            server, api = registered
            api.create_snapshot.return_value = {"snapshot_id": "s9"}

        with autotest.step("Вызываем create_snapshot"):
            result = await server.tools["create_snapshot"](_make_ctx_dict(), name="backup-1")

        with autotest.step("Проверяем диспатч и сообщение"):
            api.create_snapshot.assert_awaited_once_with(PROJECT_ID, "backup-1")
            assert result["success"] is True
            assert "backup-1" in result["message"]
            assert result["data"] == {"snapshot_id": "s9"}

    @autotest.num("817")
    @autotest.external_id("gns3-domain-tools-dispatch-start-all-nodes")
    @autotest.name("start_all_nodes: вызывает api_client.start_all_nodes, ответ без data")
    async def test_start_all_nodes_dispatch(self, registered):
        with autotest.step("Готовим api mock"):
            server, api = registered
            api.start_all_nodes.return_value = None

        with autotest.step("Вызываем start_all_nodes"):
            result = await server.tools["start_all_nodes"](_make_ctx_dict())

        with autotest.step("Проверяем диспатч и форму ответа без data"):
            api.start_all_nodes.assert_awaited_once_with(PROJECT_ID)
            assert result == {"success": True, "message": "All nodes started"}

    @autotest.num("818")
    @autotest.external_id("gns3-domain-tools-dispatch-list-templates")
    @autotest.name("list_templates: возвращает список шаблонов как есть, без обёртки")
    async def test_list_templates_dispatch(self, registered):
        with autotest.step("Готовим api mock"):
            server, api = registered
            api.list_templates.return_value = [{"template_id": "tpl-1"}]

        with autotest.step("Вызываем list_templates"):
            result = await server.tools["list_templates"](_make_ctx_dict())

        with autotest.step("Проверяем bare list passthrough"):
            api.list_templates.assert_awaited_once_with()
            assert result == [{"template_id": "tpl-1"}]
