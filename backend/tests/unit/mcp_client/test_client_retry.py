"""Unit tests for tenacity retries in MCPClient._call_tool.

Strategy: patch streamablehttp_client/ClientSession to control
exceptions and attempt counts without spinning up a real MCP server.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from tenacity import wait_exponential

from mcp_client.client import MCPClient

pytestmark = [pytest.mark.unit, pytest.mark.mcp]


def _fake_client_session_factory(session: AsyncMock):
    """Returns an async CM that yields the given fake ClientSession."""

    @asynccontextmanager
    async def fake_cs(read, write):
        yield session

    return fake_cs


def _build_call_tool_result(payload: str = '{"ok": true}'):
    """Emulate the structure of a session.call_tool result."""
    content_item = MagicMock()
    content_item.text = payload
    result = MagicMock()
    result.isError = False
    result.structuredContent = None
    result.content = [content_item]
    return result


class TestMCPClientRetry:
    @autotest.num("1830")
    @autotest.external_id("0326bce7-6376-4e0a-8acf-0aa5c55a8caa")
    @autotest.name("MCPClient._call_tool: succeeds on the second attempt after RequestError")
    async def test_0326bce7_retry_succeeds_on_second_attempt(self):
        with autotest.step("Arrange: a fake session and a transport that fails once then yields"):
            call_count = 0

            fake_session = AsyncMock()
            fake_session.initialize = AsyncMock()
            fake_session.call_tool = AsyncMock(return_value=_build_call_tool_result())

            @asynccontextmanager
            async def fake_streamable(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise httpx.RequestError("transient network blip")
                read = AsyncMock()
                write = AsyncMock()
                yield (read, write, lambda: "sid")

        with autotest.step("Act: patch streamablehttp_client and ClientSession, call _call_tool"):
            with (
                patch("mcp_client.client.streamablehttp_client", fake_streamable),
                patch(
                    "mcp_client.client.ClientSession",
                    _fake_client_session_factory(fake_session),
                ),
            ):
                client = MCPClient("http://localhost:9999", timeout=1.0)
                result = await client._call_tool("ping", {})

        with autotest.step("Check that there was exactly one retry"):
            assert_equal(call_count, 2, "expected 1 failure + 1 success")

        with autotest.step("Check that a parsed JSON result was returned"):
            assert_equal(result, {"ok": True}, "result must be the parsed JSON")

    @autotest.num("1831")
    @autotest.external_id("4ca60575-01a4-4559-8caf-b3720d28476e")
    @autotest.name("MCPClient._call_tool: 3 RequestError failures -> reraise after 3 attempts")
    async def test_4ca60575_all_attempts_fail_reraises(self):
        with autotest.step("Arrange: a transport that always fails"):
            call_count = 0

            @asynccontextmanager
            async def fake_streamable_always_fails(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                raise httpx.RequestError("persistent failure")
                yield  # pragma: no cover  # makes the function an async generator for the CM

        with (
            autotest.step("Act: patch streamablehttp_client to fail permanently"),
            patch(
                "mcp_client.client.streamablehttp_client",
                fake_streamable_always_fails,
            ),
        ):
            client = MCPClient("http://localhost:9999", timeout=1.0)

            with autotest.step("Expect a RequestError reraise after retries are exhausted"):
                with pytest.raises(httpx.RequestError):
                    await client._call_tool("ping", {})

        with autotest.step("Check the attempt count"):
            assert_equal(call_count, 3, "must be exactly 3 attempts")

    @autotest.num("1832")
    @autotest.external_id("8afd21f0-7b8f-4a40-9e00-68fc8bf350fa")
    @autotest.name("MCPClient._call_tool: tenacity config (stop_after_attempt=3)")
    def test_8afd21f0_retry_config_stop_after_attempt(self):
        with autotest.step("Get the tenacity wrapper for _call_tool"):
            retry_state = MCPClient._call_tool.retry

        with autotest.step("Check stop_after_attempt=3"):
            assert_equal(
                retry_state.stop.max_attempt_number,
                3,
                "must be 3 attempts",
            )

    @autotest.num("1833")
    @autotest.external_id("bf0341ee-4fbc-4e0e-8b7d-12641f5d716b")
    @autotest.name("MCPClient._call_tool: wait_exponential(multiplier=0.3, max=2.0)")
    def test_bf0341ee_retry_config_wait_exponential(self):
        with autotest.step("Get the tenacity wrapper"):
            wait = MCPClient._call_tool.retry.wait

        with autotest.step("Check the wait strategy type"):
            assert_true(
                isinstance(wait, wait_exponential),
                f"expected wait_exponential, got {type(wait).__name__}",
            )

        with autotest.step("Check multiplier and max"):
            assert_equal(wait.multiplier, 0.3, "multiplier must be 0.3")
            assert_equal(wait.max, 2.0, "max must be 2.0")
