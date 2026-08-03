from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from chat.router import _fetch_mcp_context
from i18n import t

pytestmark = [pytest.mark.unit]


class _Client:
    """MCP client stub returning fixed components and errors, or raising if given an Exception."""

    def __init__(self, components, errors):
        self._components = components
        self._errors = errors

    async def list_components(self, ctx):
        if isinstance(self._components, Exception):
            raise self._components
        return self._components

    async def list_errors(self, ctx):
        if isinstance(self._errors, Exception):
            raise self._errors
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
        with autotest.step("Arrange: a client with two components and one error"):
            client = _Client([_component("SW1"), _component("SW2")], [_error("link down")])

        with autotest.step("Act: fetch context in both locales"):
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
        with autotest.step("Arrange: a client with one component and no errors"):
            client = _Client([_component("SW1")], [])

        with autotest.step("Act: fetch context in both locales"):
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

    @autotest.num("3144")
    @autotest.external_id("244e2f7f-f3a8-4e1f-93de-6fbfdb1a2c88")
    @autotest.name("_fetch_mcp_context: an unreachable environment is not reported as an empty lab")
    @pytest.mark.asyncio
    async def test_244e2f7f_component_failure_is_not_empty(self):
        with autotest.step("Arrange: list_components fails while list_errors succeeds"):
            failing = _Client(RuntimeError("mcp down"), [])
            genuinely_empty = _Client([], [])

        with autotest.step("Act: fetch context for both, in both locales"):
            failed_en, _, _ = await _fetch_mcp_context(failing, None, "en")
            failed_ru, _, _ = await _fetch_mcp_context(failing, None, "ru")
            empty_en, _, _ = await _fetch_mcp_context(genuinely_empty, None, "en")

        with autotest.step("Assert: the outage is stated explicitly, not silently or as emptiness"):
            assert_true(failed_en != empty_en, "an outage must not read as a confirmed-empty lab")
            assert_true(
                t("prompt.env.components_unavailable", "en") in failed_en,
                "the tutor is told the environment could not be read",
            )
            assert_true(
                t("prompt.env.components_unavailable", "ru") in failed_ru,
                "the failure notice is localized",
            )
            assert_true(
                t("prompt.env.components_empty", "en") in empty_en,
                "a genuinely empty lab still reports as empty",
            )

    @autotest.num("3145")
    @autotest.external_id("79ca0dd8-6f84-4963-b899-d1dc817591b0")
    @autotest.name("_fetch_mcp_context: an unreadable error list is not reported as no errors")
    @pytest.mark.asyncio
    async def test_79ca0dd8_error_failure_is_not_no_errors(self):
        with autotest.step("Arrange: list_errors fails while list_components succeeds"):
            failing = _Client([_component("SW1")], RuntimeError("mcp down"))
            clean = _Client([_component("SW1")], [])

        with autotest.step("Act: fetch context for both"):
            failed_text, _, failed_count = await _fetch_mcp_context(failing, None, "en")
            clean_text, _, clean_count = await _fetch_mcp_context(clean, None, "en")

        with autotest.step("Assert: an unreadable error list is stated, not silently omitted"):
            assert_true(
                t("prompt.env.errors_unavailable", "en") in failed_text,
                "the tutor is told the error list could not be read",
            )
            assert_true(
                t("prompt.env.no_errors", "en") in clean_text,
                "a confirmed-clean environment still reports no errors",
            )
            assert_equal((failed_count, clean_count), (0, 0), "neither case invents an error count")
