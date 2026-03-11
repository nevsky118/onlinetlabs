"""Утилиты тестирования для MCP-серверов."""

from mcp_sdk.testing import reports as autotest
from mcp_sdk.testing.conformance import ConformanceTestSuite
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
from mcp_sdk.testing.utilities import (
    FakeConnectionPool,
    assert_valid_component,
    assert_valid_error_entry,
    mock_session_context,
)

__all__ = [
    "autotest",
    "ConformanceTestSuite",
    "mock_session_context",
    "assert_valid_component",
    "assert_valid_error_entry",
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
    "FakeConnectionPool",
]
