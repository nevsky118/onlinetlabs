import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from agents._shared import format_failing_check

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestFormatFailingCheck:
    @autotest.num("420")
    @autotest.external_id("e6c94f9f-8f98-4e37-8c7e-c51bbeb39b52")
    @autotest.name("format_failing_check: с узлом (node) в params")
    def test_e6c94f9f_with_node(self):
        with autotest.step("Провалившаяся проверка с params.node"):
            fc = {
                "kind": "vpcs.ping",
                "params": {"node": "PC1"},
                "expected": {"received": ">=4"},
                "actual": {"received": 0},
            }

        with autotest.step("Форматируем"):
            result = format_failing_check(fc)

        with autotest.step("Проверяем строку с node"):
            assert_equal(
                result,
                "Провалившаяся проверка vpcs.ping на PC1: "
                "ожидалось {'received': '>=4'}, получено {'received': 0}.",
                "формат с узлом",
            )

    @autotest.num("421")
    @autotest.external_id("9a72bff4-b63c-4502-88fb-9c847ab61fe3")
    @autotest.name("format_failing_check: без node в params")
    def test_9a72bff4_without_node(self):
        with autotest.step("Провалившаяся проверка без params.node"):
            fc = {
                "kind": "cisco.route",
                "params": {},
                "expected": "up",
                "actual": "down",
            }

        with autotest.step("Форматируем"):
            result = format_failing_check(fc)

        with autotest.step("Проверяем строку без ' на ...'"):
            assert_equal(
                result,
                "Провалившаяся проверка cisco.route: ожидалось up, получено down.",
                "формат без узла",
            )

    @autotest.num("422")
    @autotest.external_id("6a8096ca-382e-4e19-8736-1f504e578501")
    @autotest.name("format_failing_check: params не dict — узел не подставляется")
    def test_6a8096ca_params_not_dict(self):
        with autotest.step("params строкой, а не dict"):
            fc = {"kind": "generic.check", "params": "n/a", "expected": 1, "actual": 2}

        with autotest.step("Форматируем"):
            result = format_failing_check(fc)

        with autotest.step("Проверяем: узел не подставлен"):
            assert_equal(
                result,
                "Провалившаяся проверка generic.check: ожидалось 1, получено 2.",
                "params не dict → без узла",
            )
