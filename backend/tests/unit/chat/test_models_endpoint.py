"""Unit tests for build_models_response (pure function, no HTTP)."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in

from chat.service import build_models_response
from tests.settings.data.chat_data import (
    AgentsCatalogData,
    ModelEntryData,
    SettingsWithAgentsData,
)

pytestmark = [pytest.mark.unit]


_CATALOG = [
    ModelEntryData("claude-opus-4.8", "Claude Opus 4.8", tools=True),
    ModelEntryData("yandex-gpt-5.1", "YandexGPT 5.1", tools=False),
    ModelEntryData("claude-sonnet-4.5", "Claude Sonnet 4.5", tools=True),
]


class TestBuildModelsResponse:
    @autotest.num("790")
    @autotest.external_id("a88e6991-1166-4f5f-a99e-9e399f0fd9b6")
    @autotest.name("build_models_response: can_select=True → only tools-capable models")
    def test_a88e6991_can_select_returns_tools_models(self, monkeypatch):
        with autotest.step("Arrange: patch settings with the mixed tools/no-tools catalog"):
            monkeypatch.setattr(
                "chat.service.settings",
                SettingsWithAgentsData(AgentsCatalogData("yandex-gpt-5.1", _CATALOG)),
            )
        with autotest.step("Call with can_select=True"):
            result = build_models_response(can_select=True)
        with autotest.step("Returns only tools-capable models"):
            assert_equal(result["can_select"], True, "can select")
            assert_equal(result["default_model_id"], "yandex-gpt-5.1", "default model id")
            models = result["models"]
            assert_equal(len(models), 2, "models count")
            ids = {modelodel_2["id"] for modelodel_2 in models}
            assert_equal(ids, {"claude-opus-4.8", "claude-sonnet-4.5"}, "tools-capable models")
        with autotest.step("Each item contains id and label"):
            for modelodel_2 in models:
                assert_in("id", modelodel_2, "'id'")
                assert_in("label", modelodel_2, "'label'")

    @autotest.num("791")
    @autotest.external_id("708e1b78-2ba9-4ab5-bcd1-b87a735de6a5")
    @autotest.name("build_models_response: can_select=False → models is an empty list")
    def test_708e1b78_cannot_select_returns_empty(self, monkeypatch):
        with autotest.step("Arrange: patch settings with the mixed tools/no-tools catalog"):
            monkeypatch.setattr(
                "chat.service.settings",
                SettingsWithAgentsData(AgentsCatalogData("yandex-gpt-5.1", _CATALOG)),
            )
        with autotest.step("Call with can_select=False"):
            result = build_models_response(can_select=False)
        with autotest.step("can_select=False, models=[]"):
            assert_equal(result["can_select"], False, "can select")
            assert_equal(result["models"], [], "models")
        with autotest.step("default_model_id is present"):
            assert_equal(result["default_model_id"], "yandex-gpt-5.1", "default model id")
