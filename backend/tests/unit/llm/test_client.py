import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from config.config_model import AgentsConfig, LlmProvider, ModelEntry, ProviderCreds

pytestmark = [pytest.mark.unit]


class _FakeSettings:
    """Minimal settings stub with .agents."""

    def __init__(self, agents_config: AgentsConfig):
        self.agents = agents_config


def _yandex_agents() -> AgentsConfig:
    return AgentsConfig(
        providers={
            "yandex": ProviderCreds(
                provider=LlmProvider.YANDEX, api_key="test-key", yandex_folder="my-folder"
            )
        },
        catalog=[
            ModelEntry(
                id="yandex-gpt-5.1",
                label="YandexGPT 5.1 Pro",
                provider_ref="yandex",
                model="yandexgpt/latest",
            )
        ],
        chat_model="yandex-gpt-5.1",
        intervention_model="yandex-gpt-5.1",
    )


def _multi_agents() -> AgentsConfig:
    return AgentsConfig(
        providers={
            "yandex": ProviderCreds(provider=LlmProvider.YANDEX, api_key="yk", yandex_folder="fld"),
            "openrouter": ProviderCreds(
                provider=LlmProvider.OPENAI, api_key="ork", base_url="https://openrouter.ai/api/v1"
            ),
        },
        catalog=[
            ModelEntry(
                id="yandex-gpt-5.1",
                label="YandexGPT 5.1 Pro",
                provider_ref="yandex",
                model="yandexgpt/latest",
            ),
            ModelEntry(
                id="claude-opus-4.8",
                label="Claude Opus 4.8",
                provider_ref="openrouter",
                model="anthropic/claude-opus-4.8",
            ),
            ModelEntry(
                id="no-tools-model",
                label="No Tools",
                provider_ref="openrouter",
                model="some/model",
                tools=False,
            ),
        ],
        chat_model="yandex-gpt-5.1",
        intervention_model="yandex-gpt-5.1",
    )


@pytest.mark.unit
class TestResolveModel:
    @autotest.num("200")
    @autotest.external_id("66ac44a1-cc93-45db-b1d0-54cce63df7a5")
    @autotest.name("resolve_model: возвращает (creds, entry) по model_id")
    def test_66ac44a1_resolve_model_returns_creds_and_entry(self, monkeypatch):
        import core.llm.client as client_mod

        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_yandex_agents()))

        from core.llm.client import resolve_model

        creds, entry = resolve_model("yandex-gpt-5.1")

        with autotest.step("Проверяем provider"):
            assert_equal(creds.provider, LlmProvider.YANDEX, "provider = YANDEX")

        with autotest.step("Проверяем model id"):
            assert_equal(entry.id, "yandex-gpt-5.1", "entry.id")

    @autotest.num("201")
    @autotest.external_id("b7ffe61d-fe62-4263-8a51-bc6e7fd24ed6")
    @autotest.name("resolve_model: неизвестный model_id → KeyError")
    def test_b7ffe61d_resolve_model_unknown_raises(self, monkeypatch):
        import core.llm.client as client_mod

        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_yandex_agents()))

        from core.llm.client import resolve_model

        with autotest.step("Ожидаем KeyError на несуществующий id"):
            with pytest.raises(KeyError):
                resolve_model("nope")


@pytest.mark.unit
class TestModelUri:
    @autotest.num("202")
    @autotest.external_id("0d3311cf-fe45-4dd6-a669-0d24779fdb6e")
    @autotest.name("model_uri: yandex → gpt://<folder>/<model>")
    def test_0d3311cf_model_uri_yandex(self, monkeypatch):
        import core.llm.client as client_mod

        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_yandex_agents()))

        from core.llm.client import model_uri

        uri = model_uri("yandex-gpt-5.1")

        with autotest.step("Проверяем формат URI для Yandex"):
            assert_true(
                uri.startswith("gpt://my-folder/"), f"URI начинается с gpt://my-folder/: {uri}"
            )
            assert_equal(uri, "gpt://my-folder/yandexgpt/latest", "полный URI")

    @autotest.num("203")
    @autotest.external_id("cc3ff501-ea4c-4c3e-8b77-e64a1346ea44")
    @autotest.name("model_uri: openrouter → слаг модели")
    def test_cc3ff501_model_uri_openrouter(self, monkeypatch):
        import core.llm.client as client_mod

        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_multi_agents()))

        from core.llm.client import model_uri

        uri = model_uri("claude-opus-4.8")

        with autotest.step("Проверяем, что URI = model slug"):
            assert_equal(uri, "anthropic/claude-opus-4.8", "URI для OpenRouter = model slug")


@pytest.mark.unit
class TestModelSupportsTools:
    @autotest.num("204")
    @autotest.external_id("91b00c8b-9ce2-48a1-81f1-ca7d1cf68096")
    @autotest.name("model_supports_tools: читает ModelEntry.tools")
    def test_91b00c8b_model_supports_tools_true(self, monkeypatch):
        import core.llm.client as client_mod

        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_multi_agents()))

        from core.llm.client import model_supports_tools

        with autotest.step("tools=True по умолчанию"):
            assert_true(model_supports_tools("yandex-gpt-5.1"), "yandex-gpt-5.1 поддерживает tools")

    @autotest.num("205")
    @autotest.external_id("38adec45-a845-45d3-8f21-e0012063ba6b")
    @autotest.name("model_supports_tools: tools=False → False")
    def test_38adec45_model_supports_tools_false(self, monkeypatch):
        import core.llm.client as client_mod

        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_multi_agents()))

        from core.llm.client import model_supports_tools

        with autotest.step("tools=False возвращает False"):
            result = model_supports_tools("no-tools-model")
            assert_true(not result, "no-tools-model не поддерживает tools")


def _openrouter_with_headers_agents() -> AgentsConfig:
    return AgentsConfig(
        providers={
            "openrouter": ProviderCreds(
                provider=LlmProvider.OPENAI,
                api_key="or-key",
                base_url="https://openrouter.ai/api/v1",
                extra_headers={"HTTP-Referer": "https://example.com"},
            )
        },
        catalog=[
            ModelEntry(
                id="claude-opus-4.8",
                label="Claude Opus 4.8",
                provider_ref="openrouter",
                model="anthropic/claude-opus-4.8",
            )
        ],
        chat_model="claude-opus-4.8",
        intervention_model="claude-opus-4.8",
    )


@pytest.mark.unit
class TestBuildClient:
    @autotest.num("206")
    @autotest.external_id("ae2f409a-4e3b-43af-8243-ec8c81a27335")
    @autotest.name("build_client: возвращает AsyncOpenAI для yandex")
    def test_ae2f409a_build_client_yandex(self, monkeypatch):
        import core.llm.client as client_mod

        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_yandex_agents()))

        from openai import AsyncOpenAI

        from core.llm.client import build_client

        with autotest.step("Создаём клиент для yandex"):
            client = build_client("yandex-gpt-5.1")
            assert_true(isinstance(client, AsyncOpenAI), "результат — AsyncOpenAI")

    @autotest.num("207")
    @autotest.external_id("f7aa1cb2-46b9-4142-83b7-db0607f79104")
    @autotest.name("build_client: extra_headers провайдера попадают в AsyncOpenAI (openrouter)")
    def test_f7aa1cb2_build_client_propagates_extra_headers(self, monkeypatch):
        import core.llm.client as client_mod

        monkeypatch.setattr(
            client_mod, "settings", _FakeSettings(_openrouter_with_headers_agents())
        )

        from core.llm.client import build_client

        with autotest.step("Строим клиент для openrouter-провайдера с extra_headers"):
            client = build_client("claude-opus-4.8")

        with autotest.step("HTTP-Referer присутствует в _custom_headers клиента"):
            assert_equal(
                client._custom_headers.get("HTTP-Referer"),
                "https://example.com",
                "_custom_headers['HTTP-Referer']",
            )
