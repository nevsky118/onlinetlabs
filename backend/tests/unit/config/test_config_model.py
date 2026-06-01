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
    OpenClawConfig,
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


def _make_agents(**overrides):
    defaults = dict(api_key="sk-ant-xxx")
    return AgentsConfig(**{**defaults, **overrides})


def _make_database(**overrides):
    defaults = dict(user="u", password="p", host="localhost", port=5432, db="d")
    return DatabaseConfig(**{**defaults, **overrides})


def _make_full_config(**overrides):
    defaults = dict(
        database=_make_database(),
        redis=RedisConfig(url="redis://localhost:6379/0"),
        api=ApiConfig(environment="test", jwt_secret="s"),
        log=LogConfig(log_level="DEBUG"),
        agents=_make_agents(),
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
    @autotest.name("AgentsConfig: дефолтные значения для Anthropic")
    def test_a1b2c3d4_defaults(self):
        # Arrange
        # Act
        with autotest.step("Создаём AgentsConfig с api_key"):
            cfg = _make_agents()

        # Assert
        with autotest.step("Проверяем дефолтные значения"):
            assert_equal(
                cfg.provider, LlmProvider.ANTHROPIC, "provider должен быть ANTHROPIC"
            )
            assert_in("claude", cfg.model, "model должен содержать 'claude'")
            assert_equal(cfg.temperature, 0.3, "temperature по умолчанию 0.3")
            assert_equal(cfg.max_tokens, 4096, "max_tokens по умолчанию 4096")
            assert_equal(cfg.request_timeout, 30, "request_timeout по умолчанию 30")

    @pytest.mark.parametrize(
        "provider,extra_kwargs,error_match",
        [
            (LlmProvider.ANTHROPIC, {}, "api_key required"),
            (LlmProvider.OPENAI, {"model": "gpt-4o"}, "api_key required"),
            (
                LlmProvider.YANDEX,
                {"model": "yandexgpt/latest", "api_key": "yandex-key"},
                "yandex_folder",
            ),
        ],
    )
    @autotest.num("101")
    @autotest.external_id("b45d78d1-981d-4953-9498-2b0b78b4aebc")
    @autotest.name("AgentsConfig: провайдер требует обязательные поля")
    def test_b2c3d4e5_provider_required_fields(
        self, provider, extra_kwargs, error_match
    ):
        # Arrange
        # Act
        # Assert
        with autotest.step(f"Создаём AgentsConfig без обязательных полей для {provider}"):
            with pytest.raises(ValueError, match=error_match):
                AgentsConfig(provider=provider, **extra_kwargs)

    @pytest.mark.parametrize(
        "base_url_override,expected_base_url",
        [
            (None, "http://localhost:11434/v1"),
            ("http://192.168.1.10:11434/v1", "http://192.168.1.10:11434/v1"),
        ],
    )
    @autotest.num("103")
    @autotest.external_id("b20b522c-26e8-4b7f-9714-471423873ab4")
    @autotest.name("AgentsConfig: Ollama base_url (дефолт и кастомный)")
    def test_d4e5f6a7_ollama_base_url(self, base_url_override, expected_base_url):
        # Arrange
        kwargs = dict(provider=LlmProvider.OLLAMA, model="llama3")
        if base_url_override is not None:
            kwargs["base_url"] = base_url_override

        # Act
        with autotest.step("Создаём AgentsConfig для OLLAMA"):
            cfg = AgentsConfig(**kwargs)

        # Assert
        with autotest.step("Проверяем base_url и api_key"):
            assert_equal(
                cfg.base_url,
                expected_base_url,
                f"base_url некорректен: {cfg.base_url!r}",
            )
            assert_is_none(cfg.api_key, "api_key должен быть None для Ollama")

    @autotest.num("105")
    @autotest.external_id("bb640a7c-1fc9-4df8-aea3-ada6b5765180")
    @autotest.name("AgentsConfig: кастомные значения OpenAI")
    def test_f6a7b8c9_custom_openai_values(self):
        # Arrange
        # Act
        with autotest.step("Создаём AgentsConfig с кастомными параметрами OpenAI"):
            cfg = AgentsConfig(
                provider=LlmProvider.OPENAI,
                model="gpt-4o",
                api_key="sk-xxx",
                base_url="https://custom.endpoint.com/v1",
                temperature=0.7,
                max_tokens=2048,
                request_timeout=60,
            )

        # Assert
        with autotest.step("Проверяем кастомные значения"):
            assert_equal(
                cfg.provider, LlmProvider.OPENAI, "provider должен быть OPENAI"
            )
            assert_equal(cfg.model, "gpt-4o", "model должен быть gpt-4o")
            assert_equal(
                cfg.base_url,
                "https://custom.endpoint.com/v1",
                f"base_url некорректен: {cfg.base_url!r}",
            )


@pytest.mark.config
class TestConfigModel:
    @autotest.num("106")
    @autotest.external_id("75456dc1-509e-4e0e-8d67-24d05a96f24e")
    @autotest.name("ConfigModel: полная сборка конфигурации")
    def test_a7b8c9d0_full_config(self):
        # Arrange
        # Act
        with autotest.step("Создаём полную конфигурацию"):
            cfg = _make_full_config()

        # Assert
        with autotest.step("Проверяем поля конфигурации"):
            assert_equal(
                cfg.database.host,
                "localhost",
                f"host некорректен: {cfg.database.host!r}",
            )
            assert_equal(
                cfg.agents.provider,
                LlmProvider.ANTHROPIC,
                f"provider некорректен: {cfg.agents.provider!r}",
            )

    @autotest.num("107")
    @autotest.external_id("b8c9d0e1-f2a3-4b4c-5d6e-f7a8b9c0d1e2")
    @autotest.name("ConfigModel: отсутствие поля llm")
    def test_b8c9d0e1_no_llm_field(self):
        # Arrange
        # Act
        # Assert
        with autotest.step("Проверяем, что поле 'llm' отсутствует в ConfigModel"):
            assert_true(
                "llm" not in ConfigModel.model_fields,
                "ConfigModel не должен содержать поле 'llm'",
            )

    @autotest.num("113")
    @autotest.external_id("c5dc2a4f-85be-4233-9765-92252f3f7dab")
    @autotest.name("ConfigModel: содержит OpenClaw config")
    def test_c5dc2a4f_config_model_has_openclaw(self):
        # Arrange
        with autotest.step("Создаём OpenClawConfig"):
            openclaw = OpenClawConfig(
                enabled=True,
                base_url="http://localhost:18789",
                token="secret",
                model="openclaw",
                timeout_seconds=5.0,
            )

        # Act
        with autotest.step("Создаём полный ConfigModel"):
            cfg = _make_full_config(openclaw=openclaw)

        # Assert
        with autotest.step("Проверяем OpenClaw config"):
            assert_true(cfg.openclaw.enabled, "openclaw enabled")
            assert_equal(cfg.openclaw.base_url, "http://localhost:18789", "base_url")
            assert_equal(cfg.openclaw.token, "secret", "token")


class TestLearningAnalyticsConfig:
    @autotest.num("108")
    @autotest.external_id("c8d9e0f1-a2b3-4c4d-9e5f-a6b7c8d9e0f1")
    @autotest.name("LearningAnalyticsConfig: значения по умолчанию")
    def test_c8d9e0f1_defaults(self):
        # Arrange
        # Act
        with autotest.step("Создаём LearningAnalyticsConfig без параметров"):
            cfg = LearningAnalyticsConfig()

        # Assert
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
        # Arrange
        # Act
        with autotest.step("Создаём ConfigModel без явного learning_analytics"):
            config = _make_full_config()

        # Assert
        with autotest.step("Проверяем learning_analytics"):
            assert_true(
                config.learning_analytics is not None, "learning_analytics не None"
            )
            assert_equal(
                config.learning_analytics.poll_interval,
                5.0,
                "poll_interval по умолчанию",
            )


class TestAgentsConfigYandex:
    @pytest.mark.parametrize(
        "make_cfg,expected_uri_factory",
        [
            (
                lambda: AgentsConfig(
                    provider=LlmProvider.YANDEX,
                    api_key="yandex-key",
                    yandex_folder="b1g2h3j4k5",
                    model="yandexgpt/latest",
                    base_url="https://ai.api.cloud.yandex.net/v1",
                ),
                lambda cfg: "gpt://b1g2h3j4k5/yandexgpt/latest",
            ),
            (
                lambda: AgentsConfig(api_key="sk-test"),
                lambda cfg: cfg.model,
            ),
        ],
        ids=["yandex", "non_yandex"],
    )
    @autotest.num("110")
    @autotest.external_id("e1f2a3b4-c5d6-4e7f-8a9b-0c1d2e3f4a5b")
    @autotest.name("AgentsConfig: model_uri для разных провайдеров")
    def test_e1f2a3b4_model_uri(self, make_cfg, expected_uri_factory):
        # Arrange
        # Act
        with autotest.step("Создаём конфиг"):
            cfg = make_cfg()

        # Assert
        with autotest.step("Проверяем model_uri"):
            assert_equal(cfg.model_uri, expected_uri_factory(cfg), "model_uri")
