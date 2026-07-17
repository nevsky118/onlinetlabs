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

    @autotest.num("401")
    @autotest.external_id("2883db9b-dd6b-4bb1-9b29-7373034ad968")
    @autotest.name("BaseAgent: _agent_for не кэширует — pydantic-ai 2.x получает model per run")
    def test_2883db9b_agent_for_no_cache(self, config_model):
        with autotest.step("Создаём _Dummy агент"):
            agent = _Dummy(config_model)

        with autotest.step("Вызываем _agent_for дважды для одного model_id"):
            m1 = agent._agent_for("yandex-gpt-5.1")
            m2 = agent._agent_for("yandex-gpt-5.1")

        with autotest.step("Каждый вызов создаёт новый Agent — кэш не нужен"):
            assert_true(m1 is not m2, "_agent_for не должен переиспользовать инстанс")

    @autotest.num("402")
    @autotest.external_id("06f105f1-959d-4ec3-a324-14e25f802ba3")
    @autotest.name("BaseAgent: _build_model возвращает OpenAIChatModel для yandex")
    def test_06f105f1_build_model_yandex(self, config_model):
        from pydantic_ai.models.openai import OpenAIChatModel

        with autotest.step("Создаём _Dummy агент"):
            agent = _Dummy(config_model)

        with autotest.step("Вызываем _build_model"):
            model = agent._build_model("yandex-gpt-5.1")

        with autotest.step("Проверяем тип"):
            assert_true(
                isinstance(model, OpenAIChatModel),
                f"ожидался OpenAIChatModel, получен {type(model)}",
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

    @autotest.num("406")
    @autotest.external_id("fdbc94b5-03b1-4868-8548-e4a4e6493b62")
    @autotest.name("BaseAgent: _build_model — base_url/заголовки/model-uri для yandex")
    def test_fdbc94b5_build_model_yandex_characterization(self, config_model):
        with autotest.step("Создаём _Dummy агент"):
            agent = _Dummy(config_model)

        with autotest.step("Вызываем _build_model для yandex"):
            model = agent._build_model("yandex-gpt-5.1")

        with autotest.step("Проверяем base_url, заголовок x-folder-id, model_name клиента"):
            assert_equal(
                str(model.client.base_url),
                "https://ai.api.cloud.yandex.net/v1/",
                "base_url — дефолтный yandex endpoint",
            )
            assert_equal(
                model.client._custom_headers.get("x-folder-id"),
                "test-folder",
                "x-folder-id прокинут в заголовки",
            )
            assert_equal(
                model.model_name,
                "gpt://test-folder/yandexgpt/latest",
                "model_name — gpt:// URI",
            )

    @autotest.num("407")
    @autotest.external_id("74ebaf3a-6499-46e6-8b98-a5d950bb8673")
    @autotest.name("BaseAgent: _build_model — base_url/заголовки/model-uri для openai-совместимой модели")
    def test_74ebaf3a_build_model_openai_compatible_characterization(self, config_model):
        from config.config_model import LlmProvider, ModelEntry, ProviderCreds
        from config.env_config_loader import settings

        with autotest.step("Регистрируем openrouter-провайдера и модель в глобальном каталоге"):
            creds = ProviderCreds(
                provider=LlmProvider.OPENAI,
                api_key="sk-or-test",
                base_url="https://openrouter.ai/api/v1",
                extra_headers={"X-Title": "onlinetlabs"},
            )
            entry = ModelEntry(
                id="openrouter-test-model",
                label="test",
                provider_ref="openrouter-test",
                model="some-vendor/some-model",
            )
            original_providers = settings.agents.providers.copy()
            original_catalog = list(settings.agents.catalog)
            settings.agents.providers["openrouter-test"] = creds
            settings.agents.catalog.append(entry)

        try:
            with autotest.step("Создаём _Dummy агент и вызываем _build_model"):
                agent = _Dummy(config_model)
                model = agent._build_model("openrouter-test-model")

            with autotest.step("Проверяем base_url, заголовки, api_key, model_name клиента"):
                assert_equal(
                    str(model.client.base_url),
                    "https://openrouter.ai/api/v1/",
                    "base_url — из ProviderCreds",
                )
                assert_equal(
                    model.client._custom_headers.get("X-Title"),
                    "onlinetlabs",
                    "extra_headers прокинуты",
                )
                assert_equal(model.client.api_key, "sk-or-test", "api_key — из ProviderCreds")
                assert_equal(
                    model.model_name,
                    "some-vendor/some-model",
                    "model_name — слаг каталога",
                )
        finally:
            settings.agents.providers.clear()
            settings.agents.providers.update(original_providers)
            settings.agents.catalog[:] = original_catalog

    @autotest.num("408")
    @autotest.external_id("8dc27f60-fe66-4195-a58e-8c96dc39588b")
    @autotest.name("BaseAgent: без кэша два вызова с разными model_id используют каждый свою модель")
    def test_8dc27f60_agent_for_no_cache_picks_right_model_per_call(self, config_model):
        from config.config_model import LlmProvider, ModelEntry, ProviderCreds
        from config.env_config_loader import settings

        with autotest.step("Регистрируем второй провайдер/модель в глобальном каталоге"):
            creds = ProviderCreds(
                provider=LlmProvider.OPENAI,
                api_key="sk-second",
                base_url="https://openrouter.ai/api/v1",
            )
            entry = ModelEntry(
                id="second-model", label="second", provider_ref="second-provider",
                model="vendor/second-model",
            )
            original_providers = settings.agents.providers.copy()
            original_catalog = list(settings.agents.catalog)
            settings.agents.providers["second-provider"] = creds
            settings.agents.catalog.append(entry)

        try:
            with autotest.step("Создаём _Dummy агент и вызываем _agent_for для двух model_id"):
                agent = _Dummy(config_model)
                agent1 = agent._agent_for("yandex-gpt-5.1")
                agent2 = agent._agent_for("second-model")

            with autotest.step("Каждый вызов даёт свежий Agent с правильной моделью"):
                assert_true(agent1 is not agent2, "разные Agent-инстансы, без кэша")
                assert_equal(
                    agent1.model.model_name,
                    "gpt://test-folder/yandexgpt/latest",
                    "первый model_id → yandex uri",
                )
                assert_equal(
                    agent2.model.model_name,
                    "vendor/second-model",
                    "второй model_id → свой model_uri",
                )
        finally:
            settings.agents.providers.clear()
            settings.agents.providers.update(original_providers)
            settings.agents.catalog[:] = original_catalog

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
