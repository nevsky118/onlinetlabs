"""Unit tests for resolve_chat_model (pure function, no HTTP)."""

import pytest
from mcp_sdk.testing import autotest

from chat.router import resolve_chat_model

pytestmark = [pytest.mark.unit]


class _FakeEntry:
    pass


class _FakeAgents:
    def __init__(self, chat_default: str, ids: set[str]):
        self.chat_model = chat_default
        self._ids = ids

    def get_entry(self, model_id: str):
        return _FakeEntry() if model_id in self._ids else None


class _FakeSettings:
    def __init__(self, chat_default: str, ids: set[str]):
        self.agents = _FakeAgents(chat_default, ids)


def _fake(chat_default: str, ids: set[str]) -> _FakeSettings:
    return _FakeSettings(chat_default, ids)


class TestResolveChatModel:
    @autotest.num("780")
    @autotest.external_id("64d6a80d-2756-463d-a0b0-ab55ac873e44")
    @autotest.name("resolve_chat_model: entitled + valid id → takes the requested model")
    def test_64d6a80d_entitled_explicit_model(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1", "claude-opus-4.8"}),
        )
        with autotest.step("Entitled user requests claude-opus-4.8"):
            result = resolve_chat_model("claude-opus-4.8", None, can_select=True)
        with autotest.step("Gets the requested model"):
            assert result == "claude-opus-4.8"

    @autotest.num("781")
    @autotest.external_id("9c18bd1e-c77c-4606-8736-8ef943773314")
    @autotest.name("resolve_chat_model: not entitled → falls back to the config default")
    def test_9c18bd1e_not_entitled_falls_back(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1", "claude-opus-4.8"}),
        )
        with autotest.step("Non-entitled user requests claude-opus-4.8"):
            result = resolve_chat_model("claude-opus-4.8", None, can_select=False)
        with autotest.step("Gets the config default"):
            assert result == "yandex-gpt-5.1"

    @autotest.num("782")
    @autotest.external_id("cebf8804-ba03-4290-a2b1-cf0e66fe5467")
    @autotest.name("resolve_chat_model: invalid id → session_model_id → config default")
    def test_cebf8804_invalid_id_falls_back_to_session_then_default(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1"}),
        )
        with autotest.step("Entitled user requests ghost (not in the catalog)"):
            result = resolve_chat_model("ghost", "yandex-gpt-5.1", can_select=True)
        with autotest.step("Falls back to session_model_id"):
            assert result == "yandex-gpt-5.1"

    @autotest.num("783")
    @autotest.external_id("35c8ecfe-224f-4368-9b1a-5608549fbc8a")
    @autotest.name(
        "resolve_chat_model: no request, valid session_model_id → takes the session model"
    )
    def test_35c8ecfe_no_request_uses_session_model(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1"}),
        )
        with autotest.step("No requested, has session_model_id"):
            result = resolve_chat_model(None, "yandex-gpt-5.1", can_select=False)
        with autotest.step("Takes session_model_id"):
            assert result == "yandex-gpt-5.1"

    @autotest.num("784")
    @autotest.external_id("e0246f48-9ef0-4b25-9326-3ea039a51f3c")
    @autotest.name("resolve_chat_model: all None → config default")
    def test_e0246f48_all_none_returns_default(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1"}),
        )
        with autotest.step("Neither requested nor session_model_id"):
            result = resolve_chat_model(None, None, can_select=True)
        with autotest.step("Takes the config default"):
            assert result == "yandex-gpt-5.1"

    @autotest.num("785")
    @autotest.external_id("7159ebe9-e40d-45f0-bf58-53cda663e741")
    @autotest.name("resolve_chat_model: both invalid → config default (double fallback)")
    def test_7159ebe9_both_invalid_returns_default(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1"}),
        )
        with autotest.step("Entitled user, both requested and session_model_id invalid"):
            result = resolve_chat_model("ghost", "also-ghost", can_select=True)
        with autotest.step("Double fallback → config default"):
            assert result == "yandex-gpt-5.1"
