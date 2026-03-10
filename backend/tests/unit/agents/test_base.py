import pytest

from agents.base import BaseAgent
from config.config_model import LlmProvider
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_is_none

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestBaseAgent:
    @autotest.num("400")
    @autotest.external_id("agents-base-init")
    @autotest.name("BaseAgent: инициализация с ConfigModel")
    def test_init(self, config_model):
        with autotest.step("Создаём BaseAgent"):
            agent = BaseAgent(config_model)

        with autotest.step("Проверяем атрибуты"):
            assert_equal(agent.config, config_model, "config должен совпадать")
            assert_equal(agent.agents_config, config_model.agents, "agents_config должен совпадать")
            assert_is_none(agent._agent, "lazy agent не должен создаваться в __init__")

    @autotest.num("401")
    @autotest.external_id("agents-base-get-model-anthropic")
    @autotest.name("BaseAgent: _get_model возвращает AnthropicModel")
    def test_get_model_anthropic(self, config_model):
        from pydantic_ai.models.anthropic import AnthropicModel

        with autotest.step("Вызываем _get_model"):
            agent = BaseAgent(config_model)
            model = agent._get_model()

        with autotest.step("Проверяем тип модели"):
            assert_true(isinstance(model, AnthropicModel), f"ожидался AnthropicModel, получен {type(model)}")

    @autotest.num("402")
    @autotest.external_id("agents-base-get-model-ollama")
    @autotest.name("BaseAgent: _get_model для Ollama")
    def test_get_model_ollama(self):
        from config.config_model import AgentsConfig, ConfigModel, DatabaseConfig, RedisConfig, ApiConfig, LogConfig
        from pydantic_ai.models.openai import OpenAIModel

        with autotest.step("Создаём конфиг с Ollama"):
            cfg = ConfigModel(
                database=DatabaseConfig(user="u", password="p", host="h", port=5432, db="d"),
                redis=RedisConfig(url="redis://localhost:6379/0"),
                api=ApiConfig(environment="test", jwt_secret="s"),
                log=LogConfig(log_level="DEBUG"),
                agents=AgentsConfig(provider=LlmProvider.OLLAMA, model="llama3"),
            )
            agent = BaseAgent(cfg)
            model = agent._get_model()

        with autotest.step("Проверяем тип модели"):
            assert_true(isinstance(model, OpenAIModel), f"ожидался OpenAIModel, получен {type(model)}")

    @autotest.num("403")
    @autotest.external_id("agents-base-system-prompt-raises")
    @autotest.name("BaseAgent: system_prompt бросает NotImplementedError")
    def test_system_prompt_raises(self, config_model):
        with autotest.step("Создаём BaseAgent через __new__"):
            agent = BaseAgent.__new__(BaseAgent)
            agent.config = config_model
            agent.agents_config = config_model.agents

        with autotest.step("Вызываем system_prompt"):
            with pytest.raises(NotImplementedError):
                agent.system_prompt()

    @autotest.num("404")
    @autotest.external_id("agents-base-run-raises")
    @autotest.name("BaseAgent: run бросает NotImplementedError")
    async def test_run_raises(self, config_model):
        with autotest.step("Создаём BaseAgent через __new__"):
            agent = BaseAgent.__new__(BaseAgent)
            agent.config = config_model
            agent.agents_config = config_model.agents

        with autotest.step("Вызываем run"):
            with pytest.raises(NotImplementedError):
                await agent.run(None)

    @autotest.num("405")
    @autotest.external_id("agents-base-unsupported-provider")
    @autotest.name("BaseAgent: неподдерживаемый провайдер")
    def test_unsupported_provider(self, config_model):
        with autotest.step("Подменяем provider на невалидный"):
            agent = BaseAgent.__new__(BaseAgent)
            agent.config = config_model
            agent.agents_config = config_model.agents
            original = agent.agents_config.provider
            agent.agents_config.provider = "unknown"

        with autotest.step("Вызываем _get_model"):
            with pytest.raises(ValueError, match="Unsupported LLM provider"):
                agent._get_model()

        agent.agents_config.provider = original
