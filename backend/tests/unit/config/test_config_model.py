import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_is_none,
    assert_is_not_none,
    assert_true,
)

from config.config_model import (
    AgentsConfig,
    ApiConfig,
    ConfigModel,
    DatabaseConfig,
    GNS3Config,
    LearningAnalyticsConfig,
    LlmProvider,
    LogConfig,
    MCPConfig,
    ModelEntry,
    ProviderCreds,
    RedisConfig,
    SecurityConfig,
)

pytestmark = [pytest.mark.unit, pytest.mark.config]


def _agents(**overrides):
    base = dict(
        providers={
            "yandex": ProviderCreds(provider=LlmProvider.YANDEX, api_key="k", yandex_folder="f")
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
    return AgentsConfig(**{**base, **overrides})


def _make_database(**overrides):
    defaults = dict(user="u", password="p", host="localhost", port=5432, db="d")
    return DatabaseConfig(**{**defaults, **overrides})


def _make_full_config(**overrides):
    defaults = dict(
        database=_make_database(),
        redis=RedisConfig(url="redis://localhost:6379/0"),
        api=ApiConfig(environment="test", jwt_secret="s", frontend_url="http://localhost:3000"),
        log=LogConfig(log_level="DEBUG"),
        agents=_agents(),
        gns3=GNS3Config(
            service_url="http://gns3-service:8101",
            public_url="http://localhost:3080",
            internal_url="http://gns3-server:3080",
        ),
        mcp=MCPConfig(server_url="http://gns3-mcp:8100"),
        security=SecurityConfig(
            cred_encryption_key="r1juy4ePJMqjrYbqXaCw7kDPq8Gwudckyv0wiIBIwfU=",
            internal_api_token="test-internal-token",
        ),
    )
    return ConfigModel(**{**defaults, **overrides})


@pytest.mark.config
class TestAgentsConfig:
    @autotest.num("100")
    @autotest.external_id("c014205c-b5cb-4eff-a773-9b83d2a3e01a")
    @autotest.name("AgentsConfig: minimal valid configuration")
    def test_c014205c_defaults(self):
        with autotest.step("Create an AgentsConfig with minimal fields"):
            cfg = _agents()

        with autotest.step("Check default values"):
            assert_equal(cfg.chat_model, "yandex-gpt-5.1", "chat_model")
            assert_equal(
                cfg.interventions_follow_session,
                False,
                "interventions_follow_session defaults to False",
            )
            assert_equal(
                cfg.selectable_roles, {"student", "instructor", "admin"}, "selectable_roles"
            )
            assert_equal(cfg.temperature, 0.3, "temperature defaults to 0.3")
            assert_equal(cfg.max_tokens, 4096, "max_tokens defaults to 4096")
            assert_equal(cfg.request_timeout, 30, "request_timeout defaults to 30")

    @autotest.num("101")
    @autotest.external_id("b45d78d1-981d-4953-9498-2b0b78b4aebc")
    @autotest.name("AgentsConfig: unknown chat_model is rejected")
    def test_b45d78d1_rejects_unknown_chat_model(self):
        with autotest.step("Pass a nonexistent chat_model"), pytest.raises(ValueError):
            _agents(chat_model="does-not-exist")

    @autotest.num("102")
    @autotest.external_id("2fbf3e89-ed62-4467-9c66-45c4fe34b6f6")
    @autotest.name("AgentsConfig: ModelEntry with an unknown provider_ref is rejected")
    def test_2fbf3e89_rejects_model_with_unknown_provider_ref(self):
        with autotest.step("Pass a ModelEntry with a missing provider_ref"):
            with pytest.raises(ValueError):
                _agents(
                    catalog=[ModelEntry(id="x", label="X", provider_ref="ghost", model="m")],
                    chat_model="x",
                    intervention_model="x",
                )

    @autotest.num("103")
    @autotest.external_id("b20b522c-26e8-4b7f-9714-471423873ab4")
    @autotest.name("AgentsConfig: get_entry returns the entry by id")
    def test_b20b522c_get_entry(self):
        with autotest.step("Create a config"):
            cfg = _agents()

        with autotest.step("Look up an existing and a nonexistent entry"):
            entry = cfg.get_entry("yandex-gpt-5.1")
            assert_is_not_none(entry, "entry")
            assert_equal(entry.id, "yandex-gpt-5.1", "entry id")
            assert_is_none(cfg.get_entry("nope"), "nonexistent entry → None")

    @autotest.num("105")
    @autotest.external_id("bb640a7c-1fc9-4df8-aea3-ada6b5765180")
    @autotest.name("AgentsConfig: Ollama base_url is substituted automatically")
    def test_bb640a7c_ollama_base_url_default(self):
        with autotest.step("Create ProviderCreds for OLLAMA without base_url"):
            creds = ProviderCreds(provider=LlmProvider.OLLAMA)
            catalog = [
                ModelEntry(id="llama3", label="Llama3", provider_ref="ollama", model="llama3")
            ]
            cfg = AgentsConfig(
                providers={"ollama": creds},
                catalog=catalog,
                chat_model="llama3",
                intervention_model="llama3",
            )

        with autotest.step("Check the base_url substitution"):
            assert_equal(
                cfg.providers["ollama"].base_url,
                "http://localhost:11434/v1",
                "base_url defaults for Ollama",
            )


@pytest.mark.config
class TestConfigModel:
    @autotest.num("106")
    @autotest.external_id("75456dc1-509e-4e0e-8d67-24d05a96f24e")
    @autotest.name("ConfigModel: full config assembly")
    def test_75456dc1_full_config(self):
        with autotest.step("Create a full configuration"):
            cfg = _make_full_config()

        with autotest.step("Check the config fields"):
            assert_equal(
                cfg.database.host,
                "localhost",
                f"host is incorrect: {cfg.database.host!r}",
            )
            assert_equal(
                cfg.agents.chat_model,
                "yandex-gpt-5.1",
                f"chat_model is incorrect: {cfg.agents.chat_model!r}",
            )

    @autotest.num("107")
    @autotest.external_id("9e2811d9-d603-4112-98be-200d913cfe8a")
    @autotest.name("ConfigModel: no llm field")
    def test_9e2811d9_no_llm_field(self):
        with autotest.step("Check that the 'llm' field is absent from ConfigModel"):
            assert_true(
                "llm" not in ConfigModel.model_fields,
                "ConfigModel must not contain an 'llm' field",
            )


class TestLearningAnalyticsConfig:
    @autotest.num("108")
    @autotest.external_id("7196861d-5ca3-439a-b0ab-baff1ab1b27b")
    @autotest.name("LearningAnalyticsConfig: default values")
    def test_7196861d_defaults(self):
        with autotest.step("Create a LearningAnalyticsConfig with no parameters"):
            cfg = LearningAnalyticsConfig()

        with autotest.step("Check default values"):
            assert_equal(cfg.poll_interval, 5.0, "poll_interval = 5.0")
            assert_equal(cfg.analysis_interval, 15.0, "analysis_interval = 15.0")
            assert_equal(cfg.cooldown_period, 60.0, "cooldown_period = 60.0")
            assert_true(cfg.enabled, "enabled defaults to True")
            assert_equal(cfg.error_repeat_threshold, 3, "error_repeat_threshold = 3")

    @autotest.num("109")
    @autotest.external_id("31da00e8-cfb5-4352-9265-eabc5108cf0c")
    @autotest.name("ConfigModel: contains the learning_analytics field")
    def test_31da00e8_config_model_has_learning_analytics(self):
        with autotest.step("Create a ConfigModel without explicit learning_analytics"):
            config = _make_full_config()

        with autotest.step("Check learning_analytics"):
            assert_true(config.learning_analytics is not None, "learning_analytics is not None")
            assert_equal(
                config.learning_analytics.poll_interval,
                5.0,
                "poll_interval default",
            )
