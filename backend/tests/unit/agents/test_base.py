import pytest

from agents.base import BaseAgent
from config.config_model import LlmProvider
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_is_none

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestBaseAgent:
    @autotest.num("400")
    @autotest.external_id("b3f1a2c4-d5e6-4f7a-8b9c-0d1e2f3a4b5c")
    @autotest.name("BaseAgent: инициализация с ConfigModel")
    def test_b3f1a2c4_init(self, config_model):
        with autotest.step("Создаём BaseAgent"):
            agent = BaseAgent(config_model)

        with autotest.step("Проверяем атрибуты"):
            assert_equal(agent.config, config_model, "config должен совпадать")
            assert_equal(agent.agents_config, config_model.agents, "agents_config должен совпадать")
            assert_is_none(agent._agent, "lazy agent не должен создаваться в __init__")

    @autotest.num("401")
    @autotest.external_id("c4e2b3d5-f6a7-4b8c-9d0e-1f2a3b4c5d6e")
    @autotest.name("BaseAgent: _get_model возвращает AnthropicModel")
    def test_c4e2b3d5_get_model_anthropic(self, config_model):
        from pydantic_ai.models.anthropic import AnthropicModel

        with autotest.step("Вызываем _get_model"):
            agent = BaseAgent(config_model)
            model = agent._get_model()

        with autotest.step("Проверяем тип модели"):
            assert_true(isinstance(model, AnthropicModel), f"ожидался AnthropicModel, получен {type(model)}")

    @autotest.num("402")
    @autotest.external_id("d5f3c4e6-a7b8-4c9d-0e1f-2a3b4c5d6e7f")
    @autotest.name("BaseAgent: _get_model для Ollama")
    def test_d5f3c4e6_get_model_ollama(self):
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
    @autotest.external_id("e6a4d5f7-b8c9-4d0e-1f2a-3b4c5d6e7f8a")
    @autotest.name("BaseAgent: system_prompt бросает NotImplementedError")
    def test_e6a4d5f7_system_prompt_raises(self, config_model):
        with autotest.step("Создаём BaseAgent через __new__"):
            agent = BaseAgent.__new__(BaseAgent)
            agent.config = config_model
            agent.agents_config = config_model.agents

        with autotest.step("Вызываем system_prompt"):
            with pytest.raises(NotImplementedError):
                agent.system_prompt()

    @autotest.num("404")
    @autotest.external_id("f7b5e6a8-c9d0-4e1f-2a3b-4c5d6e7f8a9b")
    @autotest.name("BaseAgent: run бросает NotImplementedError")
    async def test_f7b5e6a8_run_raises(self, config_model):
        with autotest.step("Создаём BaseAgent через __new__"):
            agent = BaseAgent.__new__(BaseAgent)
            agent.config = config_model
            agent.agents_config = config_model.agents

        with autotest.step("Вызываем run"):
            with pytest.raises(NotImplementedError):
                await agent.run(None)

    @autotest.num("405")
    @autotest.external_id("a8c6f7b9-d0e1-4f2a-3b4c-5d6e7f8a9b0c")
    @autotest.name("BaseAgent: неподдерживаемый провайдер")
    def test_a8c6f7b9_unsupported_provider(self, config_model):
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
