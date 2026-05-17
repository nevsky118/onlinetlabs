from unittest.mock import AsyncMock

import pytest

from mcp_sdk.context import SessionContext
from mcp_sdk.errors import ActionExecutionError, SessionContextError
from mcp_sdk.testing import autotest

from src.server import ACTIONS, GNS3Server
from tests.unit.conftest import build_gns3_link, build_gns3_node, build_gns3_version

pytestmark = [pytest.mark.unit]

GNS3_URL = "http://gns3-test:3080"
PROJECT_ID = "proj-1"
NODE_ID = "node-1"
LINK_ID = "link-1"


def _make_ctx(**overrides) -> SessionContext:
    defaults = dict(
        user_id="u1",
        session_id="s1",
        environment_url=GNS3_URL,
        project_id=PROJECT_ID,
    )
    return SessionContext(**(defaults | overrides))


def _make_api_mock() -> AsyncMock:
    api = AsyncMock()
    return api


class TestGNS3ServerInit:
    @autotest.num("800")
    @autotest.external_id("gns3-server-init-stores-deps")
    @autotest.name("GNS3Server.__init__: сохраняет переданные зависимости")
    def test_init_stores_dependencies(self):
        with autotest.step("Создаём сервер с явным api_client"):
            api = _make_api_mock()
            server = GNS3Server(api_client=api, history_url="http://hist")

        with autotest.step("Проверяем поля"):
            assert server._api is api
            assert server._history_url == "http://hist"
            assert server._pool is None
            assert server._log_buffer is None


class TestActionSpecsRegistry:
    @autotest.num("801")
    @autotest.external_id("gns3-server-actions-registered")
    @autotest.name("ACTIONS: ключевые экшены зарегистрированы")
    def test_known_actions_present(self):
        with autotest.step("Собираем имена"):
            names = {action["name"] for action in ACTIONS}

        with autotest.step("Проверяем ключевые действия"):
            expected = {
                "start_node",
                "stop_node",
                "reload_node",
                "create_link",
                "delete_link",
                "start_capture",
                "create_snapshot",
            }
            assert expected.issubset(names)

    @autotest.num("802")
    @autotest.external_id("gns3-server-list-actions-no-component")
    @autotest.name("list_available_actions: без component_id возвращает все экшены")
    async def test_list_available_actions_returns_all(self):
        with autotest.step("Вызываем без component_id"):
            server = GNS3Server(api_client=_make_api_mock())
            specs = await server.list_available_actions(_make_ctx())

        with autotest.step("Все ACTIONS присутствуют"):
            assert len(specs) == len(ACTIONS)
            assert {spec.name for spec in specs} == {action["name"] for action in ACTIONS}


class TestExecuteAction:
    @autotest.num("803")
    @autotest.external_id("gns3-server-execute-start-node")
    @autotest.name("execute_action(start_node): вызывает api.start_node")
    async def test_execute_start_node_dispatches(self):
        with autotest.step("Готовим mock api"):
            api = _make_api_mock()
            server = GNS3Server(api_client=api)

        with autotest.step("Выполняем start_node"):
            result = await server.execute_action(
                _make_ctx(), "start_node", {"node_id": NODE_ID}
            )

        with autotest.step("Проверяем диспатч и успех"):
            api.start_node.assert_awaited_once_with(PROJECT_ID, NODE_ID)
            assert result.success is True

    @autotest.num("804")
    @autotest.external_id("gns3-server-execute-unknown-action")
    @autotest.name("execute_action: неизвестный экшен → ActionExecutionError")
    async def test_execute_unknown_action_raises(self):
        with autotest.step("Вызываем неизвестный экшен"):
            server = GNS3Server(api_client=_make_api_mock())

        with autotest.step("Проверяем исключение"):
            with pytest.raises(ActionExecutionError) as exc_info:
                await server.execute_action(_make_ctx(), "nuke_everything", {})
            assert exc_info.value.action_name == "nuke_everything"

    @autotest.num("805")
    @autotest.external_id("gns3-server-execute-missing-param")
    @autotest.name("execute_action: отсутствующий параметр → ActionExecutionError")
    async def test_execute_missing_param_raises(self):
        with autotest.step("Готовим сервер"):
            server = GNS3Server(api_client=_make_api_mock())

        with autotest.step("Вызываем без обязательного node_id"):
            with pytest.raises(ActionExecutionError) as exc_info:
                await server.execute_action(_make_ctx(), "start_node", {})
            assert "Missing parameter" in exc_info.value.reason


class TestStateProvider:
    @autotest.num("806")
    @autotest.external_id("gns3-server-list-components")
    @autotest.name("list_components: возвращает ноды + линки")
    async def test_list_components_aggregates(self):
        with autotest.step("Готовим mock api"):
            api = _make_api_mock()
            api.list_nodes.return_value = [
                build_gns3_node(node_id="node-1", name="R1"),
                build_gns3_node(node_id="node-2", name="R2"),
            ]
            api.list_links.return_value = [build_gns3_link()]
            server = GNS3Server(api_client=api)

        with autotest.step("Получаем компоненты"):
            components = await server.list_components(_make_ctx())

        with autotest.step("Проверяем что есть и ноды и линки"):
            assert len(components) == 3
            api.list_nodes.assert_awaited_once_with(PROJECT_ID)
            api.list_links.assert_awaited_once_with(PROJECT_ID)


class TestSessionContextErrors:
    @autotest.num("807")
    @autotest.external_id("gns3-server-missing-project-id")
    @autotest.name("execute_action: без project_id → SessionContextError")
    async def test_missing_project_id_raises(self):
        with autotest.step("Контекст без project_id"):
            server = GNS3Server(api_client=_make_api_mock())
            ctx = SessionContext(
                user_id="u1", session_id="s1", environment_url=GNS3_URL
            )

        with autotest.step("Проверяем SessionContextError"):
            with pytest.raises(SessionContextError):
                await server.execute_action(ctx, "start_all_nodes", {})
