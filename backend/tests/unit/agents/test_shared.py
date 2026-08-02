import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from agents._shared import format_failing_check

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestFormatFailingCheck:
    @autotest.num("420")
    @autotest.external_id("e6c94f9f-8f98-4e37-8c7e-c51bbeb39b52")
    @autotest.name("format_failing_check: with a node in params")
    def test_e6c94f9f_with_node(self):
        with autotest.step("Failing check with params.node"):
            fc = {
                "kind": "vpcs.ping",
                "params": {"node": "PC1"},
                "expected": {"received": ">=4"},
                "actual": {"received": 0},
            }

        with autotest.step("Format"):
            result = format_failing_check(fc, "ru")

        with autotest.step("Assert the string with node"):
            assert_equal(
                result,
                "Провалившаяся проверка vpcs.ping на PC1: "
                "ожидалось {'received': '>=4'}, получено {'received': 0}.",
                "format with node",
            )

    @autotest.num("421")
    @autotest.external_id("9a72bff4-b63c-4502-88fb-9c847ab61fe3")
    @autotest.name("format_failing_check: without node in params")
    def test_9a72bff4_without_node(self):
        with autotest.step("Failing check without params.node"):
            fc = {
                "kind": "cisco.route",
                "params": {},
                "expected": "up",
                "actual": "down",
            }

        with autotest.step("Format"):
            result = format_failing_check(fc, "ru")

        with autotest.step("Assert the string without ' on ...'"):
            assert_equal(
                result,
                "Провалившаяся проверка cisco.route: ожидалось up, получено down.",
                "format without node",
            )

    @autotest.num("422")
    @autotest.external_id("6a8096ca-382e-4e19-8736-1f504e578501")
    @autotest.name("format_failing_check: params is not a dict, node is not substituted")
    def test_6a8096ca_params_not_dict(self):
        with autotest.step("params as a string, not a dict"):
            fc = {"kind": "generic.check", "params": "n/a", "expected": 1, "actual": 2}

        with autotest.step("Format"):
            result = format_failing_check(fc, "ru")

        with autotest.step("Assert: node is not substituted"):
            assert_equal(
                result,
                "Провалившаяся проверка generic.check: ожидалось 1, получено 2.",
                "params not dict → without node",
            )
