"""Unit-тесты на tenacity-ретраи в MCPClient._call_tool.

Стратегия: патчим streamablehttp_client/ClientSession, чтобы контролировать
исключения и подсчёт попыток без поднятия реального MCP-сервера.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from tenacity import wait_exponential

from mcp_client.client import MCPClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit, pytest.mark.mcp]


def _fake_client_session_factory(session: AsyncMock):
    """Возвращает async CM, который отдаёт переданный фейковый ClientSession."""

    @asynccontextmanager
    async def fake_cs(read, write):
        yield session

    return fake_cs


def _build_call_tool_result(payload: str = '{"ok": true}'):
    """Эмулируем структуру результата session.call_tool."""
    content_item = MagicMock()
    content_item.text = payload
    result = MagicMock()
    result.isError = False
    result.structuredContent = None
    result.content = [content_item]
    return result


class TestMCPClientRetry:
    @autotest.num("1820")
    @autotest.external_id("a0b1c2d3-e4f5-4a6b-8c7d-720000000001")
    @autotest.name("MCPClient._call_tool: успех со второй попытки после RequestError")
    async def test_a0b1c2d3_retry_succeeds_on_second_attempt(self):
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

        with autotest.step("Патчим streamablehttp_client и ClientSession"):
            with (
                patch(
                    "mcp_client.client.streamablehttp_client", fake_streamable
                ),
                patch(
                    "mcp_client.client.ClientSession",
                    _fake_client_session_factory(fake_session),
                ),
            ):
                client = MCPClient("http://localhost:9999", timeout=1.0)
                result = await client._call_tool("ping", {})

        with autotest.step("Проверяем, что был ровно один ретрай"):
            assert_equal(call_count, 2, "ожидалась 1 неудача + 1 успех")

        with autotest.step("Проверяем, что вернулся распарсенный JSON-результат"):
            assert_equal(result, {"ok": True}, "результат должен быть распарсенным JSON")

    @autotest.num("1821")
    @autotest.external_id("b1c2d3e4-f5a6-4b7c-9d8e-720000000002")
    @autotest.name(
        "MCPClient._call_tool: три падения RequestError → reraise после 3 попыток"
    )
    async def test_b1c2d3e4_all_attempts_fail_reraises(self):
        call_count = 0

        @asynccontextmanager
        async def fake_streamable_always_fails(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise httpx.RequestError("persistent failure")
            yield  # pragma: no cover  # делает функцию async-генератором для CM

        with autotest.step("Патчим streamablehttp_client на постоянное падение"):
            with patch(
                "mcp_client.client.streamablehttp_client",
                fake_streamable_always_fails,
            ):
                client = MCPClient("http://localhost:9999", timeout=1.0)

                with autotest.step("Ожидаем reraise RequestError после исчерпания"):
                    with pytest.raises(httpx.RequestError):
                        await client._call_tool("ping", {})

        with autotest.step("Проверяем число попыток"):
            assert_equal(call_count, 3, "должно быть ровно 3 попытки")

    @autotest.num("1822")
    @autotest.external_id("c2d3e4f5-a6b7-4c8d-9e8f-720000000003")
    @autotest.name("MCPClient._call_tool: конфиг tenacity (stop_after_attempt=3)")
    def test_c2d3e4f5_retry_config_stop_after_attempt(self):
        with autotest.step("Достаём tenacity-обёртку с _call_tool"):
            retry_state = MCPClient._call_tool.retry

        with autotest.step("Проверяем stop_after_attempt=3"):
            assert_equal(
                retry_state.stop.max_attempt_number,
                3,
                "должно быть 3 попытки",
            )

    @autotest.num("1823")
    @autotest.external_id("d3e4f5a6-b7c8-4d9e-8a0f-720000000004")
    @autotest.name(
        "MCPClient._call_tool: wait_exponential(multiplier=0.3, max=2.0)"
    )
    def test_d3e4f5a6_retry_config_wait_exponential(self):
        with autotest.step("Достаём tenacity-обёртку"):
            wait = MCPClient._call_tool.retry.wait

        with autotest.step("Проверяем тип wait-стратегии"):
            assert_true(
                isinstance(wait, wait_exponential),
                f"ожидался wait_exponential, получен {type(wait).__name__}",
            )

        with autotest.step("Проверяем multiplier и max"):
            assert_equal(wait.multiplier, 0.3, "multiplier должен быть 0.3")
            assert_equal(wait.max, 2.0, "max должен быть 2.0")
