import pytest

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
    OpenClawConfig,
    ProviderCreds,
    RedisConfig,
    SecurityConfig,
)
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_true,
    assert_in,
    assert_is_none,
)
from mcp_sdk.testing import autotest


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
    @autotest.name("AgentsConfig: минимальная валидная конфигурация")
    def test_a1b2c3d4_defaults(self):
        with autotest.step("Создаём AgentsConfig с минимальными полями"):
            cfg = _agents()

        with autotest.step("Проверяем дефолтные значения"):
            assert_equal(cfg.chat_model, "yandex-gpt-5.1", "chat_model")
            assert_equal(
                cfg.interventions_follow_session,
                False,
                "interventions_follow_session по умолчанию False",
            )
            assert_equal(
                cfg.selectable_roles, {"student", "instructor", "admin"}, "selectable_roles"
            )
            assert_equal(cfg.temperature, 0.3, "temperature по умолчанию 0.3")
            assert_equal(cfg.max_tokens, 4096, "max_tokens по умолчанию 4096")
            assert_equal(cfg.request_timeout, 30, "request_timeout по умолчанию 30")

    @autotest.num("101")
    @autotest.external_id("b45d78d1-981d-4953-9498-2b0b78b4aebc")
    @autotest.name("AgentsConfig: неизвестная chat_model отклоняется")
    def test_b2c3d4e5_rejects_unknown_chat_model(self):
        with autotest.step("Передаём несуществующий chat_model"):
            with pytest.raises(ValueError):
                _agents(chat_model="does-not-exist")

    @autotest.num("102")
    @autotest.external_id("c3d4e5f6-b7c8-4d9e-0f1a-2b3c4d5e6f7a")
    @autotest.name("AgentsConfig: ModelEntry с неизвестным provider_ref отклоняется")
    def test_c3d4e5f6_rejects_model_with_unknown_provider_ref(self):
        with autotest.step("Передаём ModelEntry с отсутствующим provider_ref"):
            with pytest.raises(ValueError):
                _agents(
                    catalog=[ModelEntry(id="x", label="X", provider_ref="ghost", model="m")],
                    chat_model="x",
                    intervention_model="x",
                )

    @autotest.num("103")
    @autotest.external_id("b20b522c-26e8-4b7f-9714-471423873ab4")
    @autotest.name("AgentsConfig: get_entry возвращает запись по id")
    def test_d4e5f6a7_get_entry(self):
        with autotest.step("Создаём конфиг"):
            cfg = _agents()

        with autotest.step("Ищем существующую и несуществующую запись"):
            entry = cfg.get_entry("yandex-gpt-5.1")
            assert entry is not None
            assert_equal(entry.id, "yandex-gpt-5.1", "id записи")
            assert_is_none(cfg.get_entry("nope"), "несуществующая запись → None")

    @autotest.num("105")
    @autotest.external_id("bb640a7c-1fc9-4df8-aea3-ada6b5765180")
    @autotest.name("AgentsConfig: Ollama base_url подставляется автоматически")
    def test_f6a7b8c9_ollama_base_url_default(self):
        with autotest.step("Создаём ProviderCreds для OLLAMA без base_url"):
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

        with autotest.step("Проверяем подстановку base_url"):
            assert_equal(
                cfg.providers["ollama"].base_url,
                "http://localhost:11434/v1",
                "base_url для Ollama по умолчанию",
            )


@pytest.mark.config
class TestConfigModel:
    @autotest.num("106")
    @autotest.external_id("75456dc1-509e-4e0e-8d67-24d05a96f24e")
    @autotest.name("ConfigModel: полная сборка конфигурации")
    def test_a7b8c9d0_full_config(self):
        with autotest.step("Создаём полную конфигурацию"):
            cfg = _make_full_config()

        with autotest.step("Проверяем поля конфигурации"):
            assert_equal(
                cfg.database.host,
                "localhost",
                f"host некорректен: {cfg.database.host!r}",
            )
            assert_equal(
                cfg.agents.chat_model,
                "yandex-gpt-5.1",
                f"chat_model некорректен: {cfg.agents.chat_model!r}",
            )

    @autotest.num("107")
    @autotest.external_id("b8c9d0e1-f2a3-4b4c-5d6e-f7a8b9c0d1e2")
    @autotest.name("ConfigModel: отсутствие поля llm")
    def test_b8c9d0e1_no_llm_field(self):
        with autotest.step("Проверяем, что поле 'llm' отсутствует в ConfigModel"):
            assert_true(
                "llm" not in ConfigModel.model_fields,
                "ConfigModel не должен содержать поле 'llm'",
            )

    @autotest.num("113")
    @autotest.external_id("c5dc2a4f-85be-4233-9765-92252f3f7dab")
    @autotest.name("ConfigModel: содержит OpenClaw config")
    def test_c5dc2a4f_config_model_has_openclaw(self):
        with autotest.step("Создаём OpenClawConfig"):
            openclaw = OpenClawConfig(
                enabled=True,
                base_url="http://localhost:18789",
                token="secret",
                model="openclaw",
                timeout_seconds=5.0,
            )

        with autotest.step("Создаём полный ConfigModel"):
            cfg = _make_full_config(openclaw=openclaw)

        with autotest.step("Проверяем OpenClaw config"):
            assert_true(cfg.openclaw.enabled, "openclaw enabled")
            assert_equal(cfg.openclaw.base_url, "http://localhost:18789", "base_url")
            assert_equal(cfg.openclaw.token, "secret", "token")


class TestLearningAnalyticsConfig:
    @autotest.num("108")
    @autotest.external_id("c8d9e0f1-a2b3-4c4d-9e5f-a6b7c8d9e0f1")
    @autotest.name("LearningAnalyticsConfig: значения по умолчанию")
    def test_c8d9e0f1_defaults(self):
        with autotest.step("Создаём LearningAnalyticsConfig без параметров"):
            cfg = LearningAnalyticsConfig()

        with autotest.step("Проверяем значения по умолчанию"):
            assert_equal(cfg.poll_interval, 5.0, "poll_interval = 5.0")
            assert_equal(cfg.analysis_interval, 15.0, "analysis_interval = 15.0")
            assert_equal(cfg.cooldown_period, 60.0, "cooldown_period = 60.0")
            assert_true(cfg.enabled, "enabled по умолчанию True")
            assert_equal(cfg.error_repeat_threshold, 3, "error_repeat_threshold = 3")

    @autotest.num("109")
    @autotest.external_id("d9e0f1a2-b3c4-4d5e-af6b-c7d8e9f0a1b2")
    @autotest.name("ConfigModel: содержит поле learning_analytics")
    def test_d9e0f1a2_config_model_has_learning_analytics(self):
        with autotest.step("Создаём ConfigModel без явного learning_analytics"):
            config = _make_full_config()

        with autotest.step("Проверяем learning_analytics"):
            assert_true(config.learning_analytics is not None, "learning_analytics не None")
            assert_equal(
                config.learning_analytics.poll_interval,
                5.0,
                "poll_interval по умолчанию",
            )
