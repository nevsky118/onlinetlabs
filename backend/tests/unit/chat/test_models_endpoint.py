"""Unit-тесты для build_models_response (чистая функция, без HTTP)."""

import pytest
from mcp_sdk.testing import autotest

from chat.router import build_models_response

pytestmark = [pytest.mark.unit]


class _FakeEntry:
    def __init__(self, id: str, label: str, tools: bool):
        self.id = id
        self.label = label
        self.tools = tools


class _FakeAgents:
    def __init__(self, chat_model: str, catalog: list):
        self.chat_model = chat_model
        self.catalog = catalog


class _FakeSettings:
    def __init__(self, chat_model: str, catalog: list):
        self.agents = _FakeAgents(chat_model, catalog)


_CATALOG = [
    _FakeEntry("claude-opus-4.8", "Claude Opus 4.8", tools=True),
    _FakeEntry("yandex-gpt-5.1", "YandexGPT 5.1", tools=False),
    _FakeEntry("claude-sonnet-4.5", "Claude Sonnet 4.5", tools=True),
]


class TestBuildModelsResponse:

    @autotest.num("790")
    @autotest.external_id("a88e6991-1166-4f5f-a99e-9e399f0fd9b6")
    @autotest.name("build_models_response: can_select=True → только tools-capable модели")
    def test_a88e6991_can_select_returns_tools_models(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _FakeSettings("yandex-gpt-5.1", _CATALOG),
        )
        with autotest.step("Вызов с can_select=True"):
            result = build_models_response(can_select=True)
        with autotest.step("Возвращает только tools-capable модели"):
            assert result["can_select"] is True
            assert result["default_model_id"] == "yandex-gpt-5.1"
            models = result["models"]
            assert len(models) == 2
            ids = {m["id"] for m in models}
            assert ids == {"claude-opus-4.8", "claude-sonnet-4.5"}
        with autotest.step("Каждый элемент содержит id и label"):
            for m in models:
                assert "id" in m
                assert "label" in m

    @autotest.num("791")
    @autotest.external_id("708e1b78-2ba9-4ab5-bcd1-b87a735de6a5")
    @autotest.name("build_models_response: can_select=False → models пустой список")
    def test_708e1b78_cannot_select_returns_empty(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _FakeSettings("yandex-gpt-5.1", _CATALOG),
        )
        with autotest.step("Вызов с can_select=False"):
            result = build_models_response(can_select=False)
        with autotest.step("can_select=False, models=[]"):
            assert result["can_select"] is False
            assert result["models"] == []
        with autotest.step("default_model_id присутствует"):
            assert result["default_model_id"] == "yandex-gpt-5.1"
