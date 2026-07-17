import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.base import BaseAgent

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class _Dummy(BaseAgent):
    def system_prompt(self):
        return "sp"


class TestBaseAgent:
    @autotest.num("400")
    @autotest.external_id("587f52f4-94c3-451d-8c11-a3b46cded32d")
    @autotest.name("BaseAgent: инициализация с ConfigModel")
    def test_587f52f4_init(self, config_model):
        with autotest.step("Создаём BaseAgent"):
            agent = BaseAgent(config_model)

        with autotest.step("Проверяем атрибуты"):
            assert_equal(agent.config, config_model, "config должен совпадать")
            assert_equal(agent.agents_config, config_model.agents, "agents_config должен совпадать")
            assert_equal(agent._agents_by_model, {}, "кэш агентов пуст")

    @autotest.num("401")
    @autotest.external_id("2883db9b-dd6b-4bb1-9b29-7373034ad968")
    @autotest.name("BaseAgent: _agent_for кэширует по model_id")
    def test_2883db9b_agent_for_caches(self, config_model):
        with autotest.step("Создаём _Dummy агент"):
            agent = _Dummy(config_model)

        with autotest.step("Вызываем _agent_for дважды для одного model_id"):
            m1 = agent._agent_for("yandex-gpt-5.1")
            m2 = agent._agent_for("yandex-gpt-5.1")

        with autotest.step("Проверяем идентичность (кэш)"):
            assert_true(m1 is m2, "_agent_for должен возвращать тот же объект")

    @autotest.num("402")
    @autotest.external_id("06f105f1-959d-4ec3-a324-14e25f802ba3")
    @autotest.name("BaseAgent: _build_model возвращает OpenAIModel для yandex")
    def test_06f105f1_build_model_yandex(self, config_model):
        from pydantic_ai.models.openai import OpenAIModel

        with autotest.step("Создаём _Dummy агент"):
            agent = _Dummy(config_model)

        with autotest.step("Вызываем _build_model"):
            model = agent._build_model("yandex-gpt-5.1")

        with autotest.step("Проверяем тип"):
            assert_true(
                isinstance(model, OpenAIModel), f"ожидался OpenAIModel, получен {type(model)}"
            )

        with autotest.step("Проверяем model_name — gpt://<folder>/<model>"):
            # resolve_model reads global settings built from env; YANDEX_FOLDER=test-folder in conftest env
            assert_equal(
                model.model_name,
                "gpt://test-folder/yandexgpt/latest",
                "model_name должен быть gpt:// URI",
            )

    @autotest.num("405")
    @autotest.external_id("637256be-7d8b-4fb3-9da8-401877afbab9")
    @autotest.name("BaseAgent: _build_model raises ValueError если yandex_folder=None")
    def test_637256be_build_model_yandex_no_folder(self, config_model):
        with autotest.step(
            "Патчим глобальный settings.agents: yandex_folder=None через model_construct"
        ):
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
    @autotest.external_id("201db06b-9f48-4415-959a-0afe0c63842a")
    @autotest.name("BaseAgent: system_prompt бросает NotImplementedError")
    def test_201db06b_system_prompt_raises(self, config_model):
        with autotest.step("Создаём BaseAgent"):
            agent = BaseAgent(config_model)

        with autotest.step("Вызываем system_prompt"), pytest.raises(NotImplementedError):
            agent.system_prompt()

    @autotest.num("404")
    @autotest.external_id("2aaa5fea-ec64-41a1-b524-e5abb2cc168f")
    @autotest.name("BaseAgent: run бросает NotImplementedError")
    async def test_2aaa5fea_run_raises(self, config_model):
        with autotest.step("Создаём BaseAgent"):
            agent = BaseAgent(config_model)

        with autotest.step("Вызываем run"), pytest.raises(NotImplementedError):
            await agent.run(None)
