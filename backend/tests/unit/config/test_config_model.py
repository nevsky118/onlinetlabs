import pytest
from pydantic import ValidationError

from config.config_model import (
    AgentsConfig,
    ApiConfig,
    ConfigModel,
    DatabaseConfig,
    LearningAnalyticsConfig,
    LlmProvider,
    LogConfig,
    RedisConfig,
)
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_in, assert_is_none
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
    )
    return ConfigModel(**{**defaults, **overrides})


@pytest.mark.config
class TestAgentsConfig:
    @autotest.num("100")
    @autotest.external_id("a1b2c3d4-e5f6-4a7b-8c9d-e0f1a2b3c4d5")
    @autotest.name("AgentsConfig: дефолтные значения для Anthropic")
    def test_a1b2c3d4_defaults(self):
        with autotest.step("Создаём AgentsConfig с api_key"):
            cfg = _make_agents()

        with autotest.step("Проверяем дефолтные значения"):
            assert_equal(cfg.provider, LlmProvider.ANTHROPIC, "provider должен быть ANTHROPIC")
            assert_in("claude", cfg.model, "model должен содержать 'claude'")
            assert_equal(cfg.temperature, 0.3, "temperature по умолчанию 0.3")
            assert_equal(cfg.max_tokens, 4096, "max_tokens по умолчанию 4096")
            assert_equal(cfg.request_timeout, 30, "request_timeout по умолчанию 30")

    @autotest.num("101")
    @autotest.external_id("b2c3d4e5-f6a7-4b8c-9d0e-f1a2b3c4d5e6")
    @autotest.name("AgentsConfig: Anthropic требует api_key")
    def test_b2c3d4e5_anthropic_requires_api_key(self):
        with autotest.step("Создаём AgentsConfig без api_key для Anthropic"):
            with pytest.raises(ValueError, match="api_key required"):
                AgentsConfig(provider=LlmProvider.ANTHROPIC)

    @autotest.num("102")
    @autotest.external_id("c3d4e5f6-a7b8-4c9d-0e1f-a2b3c4d5e6f7")
    @autotest.name("AgentsConfig: OpenAI требует api_key")
    def test_c3d4e5f6_openai_requires_api_key(self):
        with autotest.step("Создаём AgentsConfig без api_key для OpenAI"):
            with pytest.raises(ValueError, match="api_key required"):
                AgentsConfig(provider=LlmProvider.OPENAI, model="gpt-4o")

    @autotest.num("103")
    @autotest.external_id("d4e5f6a7-b8c9-4d0e-1f2a-b3c4d5e6f7a8")
    @autotest.name("AgentsConfig: Ollama устанавливает base_url по умолчанию")
    def test_d4e5f6a7_ollama_defaults_base_url(self):
        with autotest.step("Создаём AgentsConfig с provider=OLLAMA"):
            cfg = AgentsConfig(provider=LlmProvider.OLLAMA, model="llama3")

        with autotest.step("Проверяем base_url и api_key"):
            assert_equal(
                cfg.base_url,
                "http://localhost:11434/v1",
                f"base_url некорректен: {cfg.base_url!r}",
            )
            assert_is_none(cfg.api_key, "api_key должен быть None для Ollama")

    @autotest.num("104")
    @autotest.external_id("e5f6a7b8-c9d0-4e1f-2a3b-c4d5e6f7a8b9")
    @autotest.name("AgentsConfig: Ollama принимает кастомный base_url")
    def test_e5f6a7b8_ollama_custom_base_url(self):
        with autotest.step("Создаём AgentsConfig с кастомным base_url"):
            cfg = AgentsConfig(
                provider=LlmProvider.OLLAMA,
                model="llama3",
                base_url="http://192.168.1.10:11434/v1",
            )

        with autotest.step("Проверяем кастомный base_url"):
            assert_equal(
                cfg.base_url,
                "http://192.168.1.10:11434/v1",
                f"base_url некорректен: {cfg.base_url!r}",
            )

    @autotest.num("105")
    @autotest.external_id("f6a7b8c9-d0e1-4f2a-3b4c-d5e6f7a8b9c0")
    @autotest.name("AgentsConfig: кастомные значения OpenAI")
    def test_f6a7b8c9_custom_openai_values(self):
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

        with autotest.step("Проверяем кастомные значения"):
            assert_equal(cfg.provider, LlmProvider.OPENAI, "provider должен быть OPENAI")
            assert_equal(cfg.model, "gpt-4o", "model должен быть gpt-4o")
            assert_equal(
                cfg.base_url,
                "https://custom.endpoint.com/v1",
                f"base_url некорректен: {cfg.base_url!r}",
            )


@pytest.mark.config
class TestConfigModel:
    @autotest.num("106")
    @autotest.external_id("a7b8c9d0-e1f2-4a3b-4c5d-e6f7a8b9c0d1")
    @autotest.name("ConfigModel: полная сборка конфигурации")
    def test_a7b8c9d0_full_config(self):
        with autotest.step("Создаём полную конфигурацию"):
            cfg = _make_full_config()

        with autotest.step("Проверяем поля конфигурации"):
            assert_equal(cfg.database.host, "localhost", f"host некорректен: {cfg.database.host!r}")
            assert_equal(
                cfg.agents.provider,
                LlmProvider.ANTHROPIC,
                f"provider некорректен: {cfg.agents.provider!r}",
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
            config = ConfigModel(
                database=DatabaseConfig(user="u", password="p", host="h", port=5432, db="d"),
                redis=RedisConfig(url="redis://localhost"),
                api=ApiConfig(environment="test", jwt_secret="s"),
                log=LogConfig(log_level="DEBUG"),
                agents=AgentsConfig(api_key="sk-test"),
            )

        with autotest.step("Проверяем learning_analytics"):
            assert_true(config.learning_analytics is not None, "learning_analytics не None")
            assert_equal(config.learning_analytics.poll_interval, 5.0, "poll_interval по умолчанию")


class TestAgentsConfigYandex:
    @autotest.num("110")
    @autotest.external_id("e1f2a3b4-c5d6-4e7f-8a9b-0c1d2e3f4a5b")
    @autotest.name("AgentsConfig: YANDEX model_uri формирует gpt://folder/model")
    def test_e1f2a3b4_yandex_model_uri(self):
        with autotest.step("Создаём YANDEX конфиг"):
            cfg = AgentsConfig(
                provider=LlmProvider.YANDEX,
                api_key="yandex-key",
                yandex_folder="b1g2h3j4k5",
                model="yandexgpt/latest",
                base_url="https://ai.api.cloud.yandex.net/v1",
            )
        with autotest.step("Проверяем model_uri"):
            assert_equal(cfg.model_uri, "gpt://b1g2h3j4k5/yandexgpt/latest", "model_uri")

    @autotest.num("111")
    @autotest.external_id("f2a3b4c5-d6e7-4f8a-9b0c-1d2e3f4a5b6c")
    @autotest.name("AgentsConfig: model_uri для не-YANDEX возвращает model")
    def test_f2a3b4c5_model_uri_non_yandex(self):
        with autotest.step("Создаём Anthropic конфиг"):
            cfg = AgentsConfig(api_key="sk-test")
        with autotest.step("Проверяем model_uri"):
            assert_equal(cfg.model_uri, cfg.model, "model_uri = model")

    @autotest.num("112")
    @autotest.external_id("a3b4c5d6-e7f8-4a9b-0c1d-2e3f4a5b6c7d")
    @autotest.name("AgentsConfig: YANDEX без yandex_folder бросает ошибку")
    def test_a3b4c5d6_yandex_requires_folder(self):
        with autotest.step("Пытаемся создать YANDEX без folder"):
            with pytest.raises(ValueError, match="yandex_folder"):
                AgentsConfig(
                    provider=LlmProvider.YANDEX,
                    api_key="yandex-key",
                    model="yandexgpt/latest",
                )
