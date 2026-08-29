from unittest.mock import AsyncMock

import pytest
from mcp_sdk.context import SessionContext
from mcp_sdk.errors import ActionExecutionError, SessionContextError
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in, assert_is_none, assert_true

from src.server import ACTIONS, GNS3Server
from tests.settings.data.gns3_data import Gns3LinkData, Gns3NodeData

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
    @autotest.external_id("dc102184-07cb-4720-97c0-55e2da00d6cc")
    @autotest.name("GNS3Server.__init__: stores the injected dependencies")
    def test_dc102184_init_stores_dependencies(self):
        with autotest.step("Create a server with an explicit api_client"):
            api = _make_api_mock()
            server = GNS3Server(api_client=api, history_url="http://hist")

        with autotest.step("Assert the fields"):
            assert_true(server._api is api, "server._api is api")
            assert_equal(server._history_url, "http://hist", "history url")
            assert_is_none(server._pool, "pool")
            assert_equal(server._log_buffers, {}, "log buffers")


class TestActionSpecsRegistry:
    @autotest.num("801")
    @autotest.external_id("1e6840ba-c8cf-4ebb-9dff-a87331e586f8")
    @autotest.name("ACTIONS: the key actions are registered")
    def test_1e6840ba_known_actions_present(self):
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
            assert_true(expected.issubset(names), "issubset")

    @autotest.num("802")
    @autotest.external_id("b2c4f4e1-a115-4bb4-bc04-4d62571aae7d")
    @autotest.name("list_available_actions: with no component_id, returns all actions")
    async def test_b2c4f4e1_list_available_actions_returns_all(self):
        with autotest.step("Call with no component_id"):
            server = GNS3Server(api_client=_make_api_mock())
            specs = await server.list_available_actions(_make_ctx())

        with autotest.step("All ACTIONS are present"):
            assert_equal(len(specs), len(ACTIONS), "specs count")
            assert_equal(
                {spec.name for spec in specs},
                {action["name"] for action in ACTIONS},
                "{spec.name for spec in specs}",
            )


class TestExecuteAction:
    @autotest.num("803")
    @autotest.external_id("dc9b863e-a936-4f12-a838-4e4eeb29e842")
    @autotest.name("execute_action(start_node): calls api.start_node")
    async def test_dc9b863e_execute_start_node_dispatches(self):
        with autotest.step("Set up the mock api"):
            api = _make_api_mock()
            server = GNS3Server(api_client=api)

        with autotest.step("Execute start_node"):
            result = await server.execute_action(_make_ctx(), "start_node", {"node_id": NODE_ID})

        with autotest.step("Assert the dispatch and success"):
            api.start_node.assert_awaited_once_with(PROJECT_ID, NODE_ID)
            assert_equal(result.success, True, "success")

    @autotest.num("804")
    @autotest.external_id("402c2dd5-a2df-44c1-95e7-b07570c7d3de")
    @autotest.name("execute_action: unknown action → ActionExecutionError")
    async def test_402c2dd5_execute_unknown_action_raises(self):
        with autotest.step("Call an unknown action"):
            server = GNS3Server(api_client=_make_api_mock())

        with autotest.step("Assert the exception"):
            with pytest.raises(ActionExecutionError) as exc_info:
                await server.execute_action(_make_ctx(), "nuke_everything", {})
            assert_equal(exc_info.value.action_name, "nuke_everything", "action name")

    @autotest.num("805")
    @autotest.external_id("839b172c-1751-4b67-8036-da8db3f74a70")
    @autotest.name("execute_action: missing parameter → ActionExecutionError")
    async def test_839b172c_execute_missing_param_raises(self):
        with autotest.step("Set up the server"):
            server = GNS3Server(api_client=_make_api_mock())

        with autotest.step("Call without the required node_id"):
            with pytest.raises(ActionExecutionError) as exc_info:
                await server.execute_action(_make_ctx(), "start_node", {})
            assert_in("Missing parameter", exc_info.value.reason, "'Missing parameter'")


class TestStateProvider:
    @autotest.num("806")
    @autotest.external_id("db56c9a2-d92f-4b59-b5b2-b7e61587a9e2")
    @autotest.name("list_components: returns nodes + links")
    async def test_db56c9a2_list_components_aggregates(self):
        with autotest.step("Set up the mock api"):
            api = _make_api_mock()
            api.list_nodes.return_value = [
                Gns3NodeData(node_id="node-1", name="R1").data,
                Gns3NodeData(node_id="node-2", name="R2").data,
            ]
            api.list_links.return_value = [Gns3LinkData().data]
            server = GNS3Server(api_client=api)

        with autotest.step("Get the components"):
            components = await server.list_components(_make_ctx())

        with autotest.step("Assert both nodes and links are present"):
            assert_equal(len(components), 3, "components count")
            api.list_nodes.assert_awaited_once_with(PROJECT_ID)
            api.list_links.assert_awaited_once_with(PROJECT_ID)


class TestSessionContextErrors:
    @autotest.num("807")
    @autotest.external_id("d3fb0152-24fd-4ce3-989f-f0cab55ea2f3")
    @autotest.name("execute_action: no project_id → SessionContextError")
    async def test_d3fb0152_missing_project_id_raises(self):
        with autotest.step("Context without project_id"):
            server = GNS3Server(api_client=_make_api_mock())
            ctx = SessionContext(user_id="u1", session_id="s1", environment_url=GNS3_URL)

        with autotest.step("Assert SessionContextError"):
            with pytest.raises(SessionContextError):
                await server.execute_action(ctx, "start_all_nodes", {})
