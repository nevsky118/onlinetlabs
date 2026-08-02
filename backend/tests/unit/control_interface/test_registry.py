import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none

from control_interface.registry import ToolKind, classify

pytestmark = [pytest.mark.unit]


class TestRegistry:
    @autotest.num("1730")
    @autotest.external_id("30e7764b-5a8f-43ce-be03-1c847a610431")
    @autotest.name("registry: observe/act tools are classified")
    def test_30e7764b_known_tools(self):
        with autotest.step("Assert: observation → OBSERVE, action → ACT"):
            assert_equal(classify("list_user_actions"), ToolKind.OBSERVE, "observation")
            assert_equal(classify("get_logs"), ToolKind.OBSERVE, "logs")
            assert_equal(classify("execute_action"), ToolKind.ACT, "action")

    @autotest.num("1731")
    @autotest.external_id("61cfd8a0-08f6-42c1-9eb3-69d06c453746")
    @autotest.name("registry: unclassified → None (default-deny)")
    def test_61cfd8a0_unknown_denied(self):
        with autotest.step("Assert: unknown tool → None"):
            assert_is_none(classify("rm_rf_all"), "default-deny")
