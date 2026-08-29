from unittest.mock import AsyncMock

import pytest
from mcp_sdk.context import SessionContext
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in, assert_true

from src.domain_tools import register_domain_tools
from tests.settings.data.server_data import StubServerData

pytestmark = [pytest.mark.unit, pytest.mark.domain_tools]

GNS3_URL = "http://gns3-test:3080"
PROJECT_ID = "proj-1"
NODE_ID = "node-1"
LINK_ID = "link-1"
TEMPLATE_ID = "tpl-1"
SNAPSHOT_ID = "snap-1"


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
    """Registers the domain tools on the stub server and returns (server, api_mock)."""
    server = StubServerData()
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
    # console/exec (observing device state through MCP)
    "exec_vtysh",
}


class TestRegistration:
    @autotest.num("810")
    @autotest.external_id("15c734e2-d065-4432-a133-b1029a0a8d33")
    @autotest.name("register_domain_tools: registers the full set of GNS3 tools")
    def test_15c734e2_all_expected_tools_registered(self, registered):
        with autotest.step("Get the registered names"):
            server, _ = registered
            registered_names = set(server.tools.keys())

        with autotest.step("Assert the expected tools are present"):
            assert_true(EXPECTED_TOOL_NAMES.issubset(registered_names), "issubset")

    @autotest.num("811")
    @autotest.external_id("c8e8047b-0156-44bc-b5fe-7b9397c323fe")
    @autotest.name("register_domain_tools: every tool has a non-empty description")
    def test_c8e8047b_each_tool_has_description(self, registered):
        with autotest.step("Get the descriptions"):
            server, _ = registered

        with autotest.step("All descriptions are non-empty"):
            for name in EXPECTED_TOOL_NAMES:
                assert_true(server.descriptions[name], "descriptions")


class TestDispatch:
    @autotest.num("812")
    @autotest.external_id("ddb84f7f-f616-4efe-9ebd-1fd2ab739557")
    @autotest.name("start_node: calls api_client.start_node with project_id and node_id")
    async def test_ddb84f7f_start_node_dispatch(self, registered):
        with autotest.step("Set up the api mock"):
            server, api = registered
            api.start_node.return_value = {"status": "started"}

        with autotest.step("Call start_node"):
            result = await server.tools["start_node"](_make_ctx_dict(), node_id=NODE_ID)

        with autotest.step("Assert the dispatch and response shape"):
            api.start_node.assert_awaited_once_with(PROJECT_ID, NODE_ID)
            assert_equal(result["success"], True, "success")
            assert_in(NODE_ID, result["message"], "NODE ID")
            assert_equal(result["data"], {"status": "started"}, "data")

    @autotest.num("813")
    @autotest.external_id("e0b02342-8aaf-4137-aa09-f7fadc37692d")
    @autotest.name("isolate_node: calls api_client.isolate_node")
    async def test_e0b02342_isolate_node_dispatch(self, registered):
        with autotest.step("Set up the api mock"):
            server, api = registered
            api.isolate_node.return_value = {"isolated_links": ["l1", "l2"]}

        with autotest.step("Call isolate_node"):
            result = await server.tools["isolate_node"](_make_ctx_dict(), node_id=NODE_ID)

        with autotest.step("Assert the dispatch and payload"):
            api.isolate_node.assert_awaited_once_with(PROJECT_ID, NODE_ID)
            assert_equal(result["success"], True, "success")
            assert_in("isolated", result["message"], "'isolated'")
            assert_equal(result["data"], {"isolated_links": ["l1", "l2"]}, "data")

    @autotest.num("814")
    @autotest.external_id("7b6249b3-a875-4c30-8774-8ee0b67db9b4")
    @autotest.name("get_console_info: returns the node's console fields with no success flag")
    async def test_7b6249b3_get_console_info_returns_node_fields(self, registered):
        with autotest.step("Set up the api mock"):
            server, api = registered
            api.get_node.return_value = {
                "console": 5000,
                "console_type": "telnet",
                "console_host": "127.0.0.1",
            }

        with autotest.step("Call get_console_info"):
            result = await server.tools["get_console_info"](_make_ctx_dict(), NODE_ID)

        with autotest.step("Assert the response shape"):
            api.get_node.assert_awaited_once_with(PROJECT_ID, NODE_ID)
            assert_equal(
                result,
                {
                    "node_id": NODE_ID,
                    "console": 5000,
                    "console_type": "telnet",
                    "console_host": "127.0.0.1",
                },
                "result",
            )

    @autotest.num("815")
    @autotest.external_id("e63c03a0-590d-4afa-bd30-72271695680b")
    @autotest.name("delete_link: calls api_client.delete_link, success=True")
    async def test_e63c03a0_delete_link_dispatch(self, registered):
        with autotest.step("Set up the api mock"):
            server, api = registered
            api.delete_link.return_value = None

        with autotest.step("Call delete_link"):
            result = await server.tools["delete_link"](_make_ctx_dict(), link_id=LINK_ID)

        with autotest.step("Assert"):
            api.delete_link.assert_awaited_once_with(PROJECT_ID, LINK_ID)
            assert_equal(result["success"], True, "success")
            assert_in(LINK_ID, result["message"], "LINK ID")

    @autotest.num("816")
    @autotest.external_id("c78ca492-b324-44d8-898a-dc10ff09e5eb")
    @autotest.name("create_snapshot: passes the name through to api_client.create_snapshot")
    async def test_c78ca492_create_snapshot_dispatch(self, registered):
        with autotest.step("Set up the api mock"):
            server, api = registered
            api.create_snapshot.return_value = {"snapshot_id": "s9"}

        with autotest.step("Call create_snapshot"):
            result = await server.tools["create_snapshot"](_make_ctx_dict(), name="backup-1")

        with autotest.step("Assert the dispatch and message"):
            api.create_snapshot.assert_awaited_once_with(PROJECT_ID, "backup-1")
            assert_equal(result["success"], True, "success")
            assert_in("backup-1", result["message"], "'backup-1'")
            assert_equal(result["data"], {"snapshot_id": "s9"}, "data")

    @autotest.num("817")
    @autotest.external_id("9813319e-ec2b-43ee-930e-c1b4e82b3d92")
    @autotest.name("start_all_nodes: calls api_client.start_all_nodes, response has no data")
    async def test_9813319e_start_all_nodes_dispatch(self, registered):
        with autotest.step("Set up the api mock"):
            server, api = registered
            api.start_all_nodes.return_value = None

        with autotest.step("Call start_all_nodes"):
            result = await server.tools["start_all_nodes"](_make_ctx_dict())

        with autotest.step("Assert the dispatch and the data-less response shape"):
            api.start_all_nodes.assert_awaited_once_with(PROJECT_ID)
            assert_equal(result, {"success": True, "message": "All nodes started"}, "result")

    @autotest.num("818")
    @autotest.external_id("5ea26e02-71f7-42cf-9579-166f7577d3d7")
    @autotest.name("list_templates: returns the template list as-is, unwrapped")
    async def test_5ea26e02_list_templates_dispatch(self, registered):
        with autotest.step("Set up the api mock"):
            server, api = registered
            api.list_templates.return_value = [{"template_id": "tpl-1"}]

        with autotest.step("Call list_templates"):
            result = await server.tools["list_templates"](_make_ctx_dict())

        with autotest.step("Assert the bare list passthrough"):
            api.list_templates.assert_awaited_once_with()
            assert_equal(result, [{"template_id": "tpl-1"}], "result")
