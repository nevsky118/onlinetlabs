"""Утилиты тестирования для MCP-серверов."""

from mcp_sdk.testing import reports as autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_false,
    assert_greater,
    assert_greater_equal,
    assert_in,
    assert_is_instance,
    assert_is_none,
    assert_is_not_none,
    assert_less,
    assert_less_equal,
    assert_not_equal,
    assert_true,
)

__all__ = [
    "assert_equal",
    "assert_false",
    "assert_greater",
    "assert_greater_equal",
    "assert_in",
    "assert_is_instance",
    "assert_is_none",
    "assert_is_not_none",
    "assert_less",
    "assert_less_equal",
    "assert_not_equal",
    "assert_true",
    "autotest",
]
