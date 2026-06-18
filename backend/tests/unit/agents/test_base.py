import pytest

from agents.base import BaseAgent
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_false

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class _Dummy(BaseAgent):
    def system_prompt(self):
        return "sp"


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
            assert_equal(agent._agents_by_model, {}, "кэш агентов пуст")

    @autotest.num("401")
    @autotest.external_id("c4e2b3d5-f6a7-4b8c-9d0e-1f2a3b4c5d6e")
    @autotest.name("BaseAgent: _agent_for кэширует по model_id")
    def test_c4e2b3d5_agent_for_caches(self, config_model):
        with autotest.step("Создаём _Dummy агент"):
            agent = _Dummy(config_model)

        with autotest.step("Вызываем _agent_for дважды для одного model_id"):
            m1 = agent._agent_for("yandex-gpt-5.1")
            m2 = agent._agent_for("yandex-gpt-5.1")

        with autotest.step("Проверяем идентичность (кэш)"):
            assert_true(m1 is m2, "_agent_for должен возвращать тот же объект")

    @autotest.num("402")
    @autotest.external_id("d5f3c4e6-a7b8-4c9d-0e1f-2a3b4c5d6e7f")
    @autotest.name("BaseAgent: _build_model возвращает OpenAIModel для yandex")
    def test_d5f3c4e6_build_model_yandex(self, config_model):
        from pydantic_ai.models.openai import OpenAIModel

        with autotest.step("Создаём _Dummy агент"):
            agent = _Dummy(config_model)

        with autotest.step("Вызываем _build_model"):
            model = agent._build_model("yandex-gpt-5.1")

        with autotest.step("Проверяем тип"):
            assert_true(isinstance(model, OpenAIModel), f"ожидался OpenAIModel, получен {type(model)}")

        with autotest.step("Проверяем model_name — gpt://<folder>/<model>"):
            # resolve_model reads global settings built from env; YANDEX_FOLDER=test-folder in conftest env
            assert_equal(model.model_name, "gpt://test-folder/yandexgpt/latest", "model_name должен быть gpt:// URI")

    @autotest.num("405")
    @autotest.external_id("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
    @autotest.name("BaseAgent: _build_model raises ValueError если yandex_folder=None")
    def test_a1b2c3d4_build_model_yandex_no_folder(self, config_model):
        with autotest.step("Патчим глобальный settings.agents: yandex_folder=None через model_construct"):
            from config.config_model import LlmProvider, ProviderCreds
            from config.env_config_loader import settings

            creds_no_folder = ProviderCreds.model_construct(
                provider=LlmProvider.YANDEX,
                api_key="k",
                yandex_folder=None,
                base_url=None,
                extra_headers=None,
            )
            original_providers = settings.agents.providers.copy()
            settings.agents.providers["yandex"] = creds_no_folder

        try:
            with autotest.step("_build_model должен бросить ValueError"):
                agent = _Dummy(config_model)
                with pytest.raises(ValueError, match="yandex_folder required"):
                    agent._build_model("yandex-gpt-5.1")
        finally:
            settings.agents.providers.update(original_providers)

    @autotest.num("403")
    @autotest.external_id("e6a4d5f7-b8c9-4d0e-1f2a-3b4c5d6e7f8a")
    @autotest.name("BaseAgent: system_prompt бросает NotImplementedError")
    def test_e6a4d5f7_system_prompt_raises(self, config_model):
        with autotest.step("Создаём BaseAgent"):
            agent = BaseAgent(config_model)

        with autotest.step("Вызываем system_prompt"):
            with pytest.raises(NotImplementedError):
                agent.system_prompt()

    @autotest.num("404")
    @autotest.external_id("f7b5e6a8-c9d0-4e1f-2a3b-4c5d6e7f8a9b")
    @autotest.name("BaseAgent: run бросает NotImplementedError")
    async def test_f7b5e6a8_run_raises(self, config_model):
        with autotest.step("Создаём BaseAgent"):
            agent = BaseAgent(config_model)

        with autotest.step("Вызываем run"):
            with pytest.raises(NotImplementedError):
                await agent.run(None)
