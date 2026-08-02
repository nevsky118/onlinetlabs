from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from chat.router import _fetch_mcp_context

pytestmark = [pytest.mark.unit]


class _Client:
    """MCP client stub returning fixed components and errors."""

    def __init__(self, components, errors):
        self._components = components
        self._errors = errors

    async def list_components(self, ctx):
        return self._components

    async def list_errors(self, ctx):
        return self._errors


def _component(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, type="ethernet_switch", status="started", summary="ok")


def _error(message: str) -> SimpleNamespace:
    return SimpleNamespace(level=SimpleNamespace(value="error"), component_id="n1", message=message)


class TestMcpContextCounts:
    @autotest.num("3133")
    @autotest.external_id("694fcab8-6e63-4392-abc2-a236368fe0b4")
    @autotest.name("_fetch_mcp_context: counts are structural, not parsed from the prompt text")
    @pytest.mark.asyncio
    async def test_694fcab8_counts_are_structural(self):
        with autotest.step("Act: fetch context with two components and one error, in both locales"):
            client = _Client([_component("SW1"), _component("SW2")], [_error("link down")])
            _, en_components, en_errors = await _fetch_mcp_context(client, None, "en")
            _, ru_components, ru_errors = await _fetch_mcp_context(client, None, "ru")

        with autotest.step("Assert: the counts are identical across locales"):
            assert_equal((en_components, en_errors), (2, 1), "en counts are structural")
            assert_equal((ru_components, ru_errors), (2, 1), "ru counts match en")

    @autotest.num("3134")
    @autotest.external_id("2c64c427-749c-4d2e-82ea-ea5142f888b8")
    @autotest.name("_fetch_mcp_context: a clean environment reports zero errors in both locales")
    @pytest.mark.asyncio
    async def test_2c64c427_zero_errors(self):
        with autotest.step("Act: fetch context with no errors"):
            client = _Client([_component("SW1")], [])
            _, _, en_errors = await _fetch_mcp_context(client, None, "en")
            _, _, ru_errors = await _fetch_mcp_context(client, None, "ru")

        with autotest.step("Assert: both report zero"):
            assert_equal((en_errors, ru_errors), (0, 0), "no errors means zero in both locales")

    @autotest.num("3135")
    @autotest.external_id("ea0392bf-8b90-4c6d-bdb8-8667cb0f6be2")
    @autotest.name("_fetch_mcp_context: a missing client yields no context and zero counts")
    @pytest.mark.asyncio
    async def test_ea0392bf_no_client(self):
        with autotest.step("Act: fetch context without an MCP client"):
            text, components, errors = await _fetch_mcp_context(None, None, "en")

        with autotest.step("Assert: the caller gets a usable triple rather than a bare None"):
            assert_equal((text, components, errors), (None, 0, 0), "absent client is not an error")
