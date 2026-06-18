import pytest

from config.config_model import AgentsConfig, ModelEntry, ProviderCreds, LlmProvider
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class _FakeSettings:
    """Минимальная заглушка settings с .agents."""

    def __init__(self, agents_config: AgentsConfig):
        self.agents = agents_config


def _yandex_agents() -> AgentsConfig:
    return AgentsConfig(
        providers={"yandex": ProviderCreds(provider=LlmProvider.YANDEX, api_key="test-key", yandex_folder="my-folder")},
        catalog=[ModelEntry(id="yandex-gpt-5.1", label="YandexGPT 5.1 Pro",
                            provider_ref="yandex", model="yandexgpt/latest")],
        chat_model="yandex-gpt-5.1",
        intervention_model="yandex-gpt-5.1",
    )


def _multi_agents() -> AgentsConfig:
    return AgentsConfig(
        providers={
            "yandex": ProviderCreds(provider=LlmProvider.YANDEX, api_key="yk", yandex_folder="fld"),
            "openrouter": ProviderCreds(provider=LlmProvider.OPENAI, api_key="ork",
                                        base_url="https://openrouter.ai/api/v1"),
        },
        catalog=[
            ModelEntry(id="yandex-gpt-5.1", label="YandexGPT 5.1 Pro",
                       provider_ref="yandex", model="yandexgpt/latest"),
            ModelEntry(id="claude-opus-4.8", label="Claude Opus 4.8",
                       provider_ref="openrouter", model="anthropic/claude-opus-4.8"),
            ModelEntry(id="no-tools-model", label="No Tools", provider_ref="openrouter",
                       model="some/model", tools=False),
        ],
        chat_model="yandex-gpt-5.1",
        intervention_model="yandex-gpt-5.1",
    )


@pytest.mark.unit
class TestResolveModel:
    @autotest.num("200")
    @autotest.external_id("a1b2c3d4-0001-4000-8000-000000000001")
    @autotest.name("resolve_model: возвращает (creds, entry) по model_id")
    def test_resolve_model_returns_creds_and_entry(self, monkeypatch):
        import llm.client as client_mod
        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_yandex_agents()))

        from llm.client import resolve_model
        creds, entry = resolve_model("yandex-gpt-5.1")

        with autotest.step("Проверяем provider"):
            assert_equal(creds.provider, LlmProvider.YANDEX, "provider = YANDEX")

        with autotest.step("Проверяем model id"):
            assert_equal(entry.id, "yandex-gpt-5.1", "entry.id")

    @autotest.num("201")
    @autotest.external_id("a1b2c3d4-0001-4000-8000-000000000002")
    @autotest.name("resolve_model: неизвестный model_id → KeyError")
    def test_resolve_model_unknown_raises(self, monkeypatch):
        import llm.client as client_mod
        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_yandex_agents()))

        from llm.client import resolve_model
        with autotest.step("Ожидаем KeyError на несуществующий id"):
            with pytest.raises(KeyError):
                resolve_model("nope")


@pytest.mark.unit
class TestModelUri:
    @autotest.num("202")
    @autotest.external_id("a1b2c3d4-0001-4000-8000-000000000003")
    @autotest.name("model_uri: yandex → gpt://<folder>/<model>")
    def test_model_uri_yandex(self, monkeypatch):
        import llm.client as client_mod
        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_yandex_agents()))

        from llm.client import model_uri
        uri = model_uri("yandex-gpt-5.1")

        with autotest.step("Проверяем формат URI для Yandex"):
            assert_true(uri.startswith("gpt://my-folder/"), f"URI начинается с gpt://my-folder/: {uri}")
            assert_equal(uri, "gpt://my-folder/yandexgpt/latest", "полный URI")

    @autotest.num("203")
    @autotest.external_id("a1b2c3d4-0001-4000-8000-000000000004")
    @autotest.name("model_uri: openrouter → слаг модели")
    def test_model_uri_openrouter(self, monkeypatch):
        import llm.client as client_mod
        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_multi_agents()))

        from llm.client import model_uri
        uri = model_uri("claude-opus-4.8")

        with autotest.step("Проверяем, что URI = model slug"):
            assert_equal(uri, "anthropic/claude-opus-4.8", "URI для OpenRouter = model slug")


@pytest.mark.unit
class TestModelSupportsTools:
    @autotest.num("204")
    @autotest.external_id("a1b2c3d4-0001-4000-8000-000000000005")
    @autotest.name("model_supports_tools: читает ModelEntry.tools")
    def test_model_supports_tools_true(self, monkeypatch):
        import llm.client as client_mod
        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_multi_agents()))

        from llm.client import model_supports_tools
        with autotest.step("tools=True по умолчанию"):
            assert_true(model_supports_tools("yandex-gpt-5.1"), "yandex-gpt-5.1 поддерживает tools")

    @autotest.num("205")
    @autotest.external_id("a1b2c3d4-0001-4000-8000-000000000006")
    @autotest.name("model_supports_tools: tools=False → False")
    def test_model_supports_tools_false(self, monkeypatch):
        import llm.client as client_mod
        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_multi_agents()))

        from llm.client import model_supports_tools
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
        catalog=[ModelEntry(id="claude-opus-4.8", label="Claude Opus 4.8",
                            provider_ref="openrouter", model="anthropic/claude-opus-4.8")],
        chat_model="claude-opus-4.8",
        intervention_model="claude-opus-4.8",
    )


@pytest.mark.unit
class TestBuildClient:
    @autotest.num("206")
    @autotest.external_id("a1b2c3d4-0001-4000-8000-000000000007")
    @autotest.name("build_client: возвращает AsyncOpenAI для yandex")
    def test_build_client_yandex(self, monkeypatch):
        import llm.client as client_mod
        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_yandex_agents()))

        from openai import AsyncOpenAI
        from llm.client import build_client
        with autotest.step("Создаём клиент для yandex"):
            client = build_client("yandex-gpt-5.1")
            assert_true(isinstance(client, AsyncOpenAI), "результат — AsyncOpenAI")

    @autotest.num("207")
    @autotest.external_id("a1b2c3d4-0001-4000-8000-000000000008")
    @autotest.name("build_client: extra_headers провайдера попадают в AsyncOpenAI (openrouter)")
    def test_build_client_propagates_extra_headers(self, monkeypatch):
        import llm.client as client_mod
        monkeypatch.setattr(client_mod, "settings", _FakeSettings(_openrouter_with_headers_agents()))

        from llm.client import build_client
        with autotest.step("Строим клиент для openrouter-провайдера с extra_headers"):
            client = build_client("claude-opus-4.8")

        with autotest.step("HTTP-Referer присутствует в _custom_headers клиента"):
            assert_equal(
                client._custom_headers.get("HTTP-Referer"),
                "https://example.com",
                "_custom_headers['HTTP-Referer']",
            )
