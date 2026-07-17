"""Sanity check for chat/router.py constants."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from chat.router import MAX_TOOL_ROUNDS

pytestmark = [pytest.mark.unit]


class TestRouterConstants:
    @autotest.num("770")
    @autotest.external_id("5d0b1f3a-7e91-4c82-9b6d-2a4f8c1d3e5b")
    @autotest.name("MAX_TOOL_ROUNDS == 5, защита от бесконечного цикла инструментов")
    def test_5d0b1f3a_max_tool_rounds_is_5(self):
        with autotest.step("Проверяем значение константы"):
            assert_equal(MAX_TOOL_ROUNDS, 5, "MAX_TOOL_ROUNDS")
