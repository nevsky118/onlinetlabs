from unittest.mock import AsyncMock

import pytest
from mcp_sdk.context import SessionContext
from mcp_sdk.errors import ActionExecutionError, SessionContextError
from mcp_sdk.testing import autotest

from src.server import ACTIONS, GNS3Server
from tests.unit.conftest import build_gns3_link, build_gns3_node

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
    @autotest.name("GNS3Server.__init__: stores the injected dependencies")
    def test_init_stores_dependencies(self):
        with autotest.step("Create a server with an explicit api_client"):
            api = _make_api_mock()
            server = GNS3Server(api_client=api, history_url="http://hist")

        with autotest.step("Assert the fields"):
            assert server._api is api
            assert server._history_url == "http://hist"
            assert server._pool is None
            assert server._log_buffers == {}


class TestActionSpecsRegistry:
    @autotest.num("801")
    @autotest.external_id("gns3-server-actions-registered")
    @autotest.name("ACTIONS: the key actions are registered")
    def test_known_actions_present(self):
        with autotest.step("Collect the names"):
            names = {action["name"] for action in ACTIONS}

        with autotest.step("Assert the key actions"):
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
    @autotest.name("list_available_actions: with no component_id, returns all actions")
    async def test_list_available_actions_returns_all(self):
        with autotest.step("Call with no component_id"):
            server = GNS3Server(api_client=_make_api_mock())
            specs = await server.list_available_actions(_make_ctx())

        with autotest.step("All ACTIONS are present"):
            assert len(specs) == len(ACTIONS)
            assert {spec.name for spec in specs} == {action["name"] for action in ACTIONS}


class TestExecuteAction:
    @autotest.num("803")
    @autotest.external_id("gns3-server-execute-start-node")
    @autotest.name("execute_action(start_node): calls api.start_node")
    async def test_execute_start_node_dispatches(self):
        with autotest.step("Set up the mock api"):
            api = _make_api_mock()
            server = GNS3Server(api_client=api)

        with autotest.step("Execute start_node"):
            result = await server.execute_action(_make_ctx(), "start_node", {"node_id": NODE_ID})

        with autotest.step("Assert the dispatch and success"):
            api.start_node.assert_awaited_once_with(PROJECT_ID, NODE_ID)
            assert result.success is True

    @autotest.num("804")
    @autotest.external_id("gns3-server-execute-unknown-action")
    @autotest.name("execute_action: unknown action → ActionExecutionError")
    async def test_execute_unknown_action_raises(self):
        with autotest.step("Call an unknown action"):
            server = GNS3Server(api_client=_make_api_mock())

        with autotest.step("Assert the exception"):
            with pytest.raises(ActionExecutionError) as exc_info:
                await server.execute_action(_make_ctx(), "nuke_everything", {})
            assert exc_info.value.action_name == "nuke_everything"

    @autotest.num("805")
    @autotest.external_id("gns3-server-execute-missing-param")
    @autotest.name("execute_action: missing parameter → ActionExecutionError")
    async def test_execute_missing_param_raises(self):
        with autotest.step("Set up the server"):
            server = GNS3Server(api_client=_make_api_mock())

        with autotest.step("Call without the required node_id"):
            with pytest.raises(ActionExecutionError) as exc_info:
                await server.execute_action(_make_ctx(), "start_node", {})
            assert "Missing parameter" in exc_info.value.reason


class TestStateProvider:
    @autotest.num("806")
    @autotest.external_id("gns3-server-list-components")
    @autotest.name("list_components: returns nodes + links")
    async def test_list_components_aggregates(self):
        with autotest.step("Set up the mock api"):
            api = _make_api_mock()
            api.list_nodes.return_value = [
                build_gns3_node(node_id="node-1", name="R1"),
                build_gns3_node(node_id="node-2", name="R2"),
            ]
            api.list_links.return_value = [build_gns3_link()]
            server = GNS3Server(api_client=api)

        with autotest.step("Get the components"):
            components = await server.list_components(_make_ctx())

        with autotest.step("Assert both nodes and links are present"):
            assert len(components) == 3
            api.list_nodes.assert_awaited_once_with(PROJECT_ID)
            api.list_links.assert_awaited_once_with(PROJECT_ID)


class TestSessionContextErrors:
    @autotest.num("807")
    @autotest.external_id("gns3-server-missing-project-id")
    @autotest.name("execute_action: no project_id → SessionContextError")
    async def test_missing_project_id_raises(self):
        with autotest.step("Context without project_id"):
            server = GNS3Server(api_client=_make_api_mock())
            ctx = SessionContext(user_id="u1", session_id="s1", environment_url=GNS3_URL)

        with autotest.step("Assert SessionContextError"):
            with pytest.raises(SessionContextError):
                await server.execute_action(ctx, "start_all_nodes", {})
