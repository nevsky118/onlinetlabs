"""Unit-тесты для resolve_chat_model (чистая функция, без HTTP)."""

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
    @autotest.external_id("a1b2c3d4-0001-4000-8000-000000000001")
    @autotest.name("resolve_chat_model: entitled + valid id → берёт запрошенную модель")
    def test_a1b2c3d4_entitled_explicit_model(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1", "claude-opus-4.8"}),
        )
        with autotest.step("Entitled пользователь запрашивает claude-opus-4.8"):
            result = resolve_chat_model("claude-opus-4.8", None, can_select=True)
        with autotest.step("Получает запрошенную модель"):
            assert result == "claude-opus-4.8"

    @autotest.num("781")
    @autotest.external_id("a1b2c3d4-0002-4000-8000-000000000002")
    @autotest.name("resolve_chat_model: not entitled → фолбэк на config-дефолт")
    def test_a1b2c3d4_not_entitled_falls_back(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1", "claude-opus-4.8"}),
        )
        with autotest.step("Не-entitled пользователь запрашивает claude-opus-4.8"):
            result = resolve_chat_model("claude-opus-4.8", None, can_select=False)
        with autotest.step("Получает config-дефолт"):
            assert result == "yandex-gpt-5.1"

    @autotest.num("782")
    @autotest.external_id("a1b2c3d4-0003-4000-8000-000000000003")
    @autotest.name("resolve_chat_model: invalid id → session_model_id → config-дефолт")
    def test_a1b2c3d4_invalid_id_falls_back_to_session_then_default(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1"}),
        )
        with autotest.step("Entitled пользователь запрашивает ghost (нет в каталоге)"):
            result = resolve_chat_model("ghost", "yandex-gpt-5.1", can_select=True)
        with autotest.step("Фолбэк на session_model_id"):
            assert result == "yandex-gpt-5.1"

    @autotest.num("783")
    @autotest.external_id("a1b2c3d4-0004-4000-8000-000000000004")
    @autotest.name("resolve_chat_model: no request, valid session_model_id → берёт сессию")
    def test_a1b2c3d4_no_request_uses_session_model(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1"}),
        )
        with autotest.step("Нет requested, есть session_model_id"):
            result = resolve_chat_model(None, "yandex-gpt-5.1", can_select=False)
        with autotest.step("Берёт session_model_id"):
            assert result == "yandex-gpt-5.1"

    @autotest.num("784")
    @autotest.external_id("a1b2c3d4-0005-4000-8000-000000000005")
    @autotest.name("resolve_chat_model: все None → config-дефолт")
    def test_a1b2c3d4_all_none_returns_default(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1"}),
        )
        with autotest.step("Нет ни requested, ни session_model_id"):
            result = resolve_chat_model(None, None, can_select=True)
        with autotest.step("Берёт config-дефолт"):
            assert result == "yandex-gpt-5.1"

    @autotest.num("785")
    @autotest.external_id("a1b2c3d4-0006-4000-8000-000000000006")
    @autotest.name("resolve_chat_model: оба invalid → config-дефолт (двойной фолбэк)")
    def test_a1b2c3d4_both_invalid_returns_default(self, monkeypatch):
        monkeypatch.setattr(
            "chat.router.settings",
            _fake(chat_default="yandex-gpt-5.1", ids={"yandex-gpt-5.1"}),
        )
        with autotest.step("Entitled пользователь, оба requested и session_model_id invalid"):
            result = resolve_chat_model("ghost", "also-ghost", can_select=True)
        with autotest.step("Двойной фолбэк → config-дефолт"):
            assert result == "yandex-gpt-5.1"
