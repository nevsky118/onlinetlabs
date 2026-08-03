import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.base import BaseAgent

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class _Dummy(BaseAgent):
    def system_prompt(self, locale):
        return "sp"


class TestBaseAgent:
    @autotest.num("400")
    @autotest.external_id("587f52f4-94c3-451d-8c11-a3b46cded32d")
    @autotest.name("BaseAgent: initialization with ConfigModel")
    def test_587f52f4_init(self, config_model):
        with autotest.step("Create BaseAgent"):
            agent = BaseAgent(config_model)

        with autotest.step("Assert attributes"):
            assert_equal(agent.config, config_model, "config should match")
            assert_equal(agent.agents_config, config_model.agents, "agents_config should match")

    @autotest.num("401")
    @autotest.external_id("2883db9b-dd6b-4bb1-9b29-7373034ad968")
    @autotest.name("BaseAgent: _agent_for doesn't cache, pydantic-ai 2.x gets model per run")
    def test_2883db9b_agent_for_no_cache(self, config_model):
        with autotest.step("Create _Dummy agent"):
            agent = _Dummy(config_model)

        with autotest.step("Call _agent_for twice for the same model_id"):
            m1 = agent._agent_for("yandex-gpt-5.1", "en")
            m2 = agent._agent_for("yandex-gpt-5.1", "en")

        with autotest.step("Each call creates a new Agent, no cache needed"):
            assert_true(m1 is not m2, "_agent_for should not reuse the instance")

    @autotest.num("402")
    @autotest.external_id("06f105f1-959d-4ec3-a324-14e25f802ba3")
    @autotest.name("BaseAgent: _build_model returns OpenAIChatModel for yandex")
    def test_06f105f1_build_model_yandex(self, config_model):
        with autotest.step("Arrange: import OpenAIChatModel"):
            from pydantic_ai.models.openai import OpenAIChatModel

        with autotest.step("Create _Dummy agent"):
            agent = _Dummy(config_model)

        with autotest.step("Call _build_model"):
            model = agent._build_model("yandex-gpt-5.1")

        with autotest.step("Assert type"):
            assert_true(
                isinstance(model, OpenAIChatModel),
                f"expected OpenAIChatModel, got {type(model)}",
            )

        with autotest.step("Assert model_name gpt://<folder>/<model>"):
            # resolve_model reads global settings built from env; YANDEX_FOLDER=test-folder in conftest env
            assert_equal(
                model.model_name,
                "gpt://test-folder/yandexgpt/latest",
                "model_name should be a gpt:// URI",
            )

    @autotest.num("405")
    @autotest.external_id("637256be-7d8b-4fb3-9da8-401877afbab9")
    @autotest.name("BaseAgent: _build_model raises ValueError when yandex_folder=None")
    def test_637256be_build_model_yandex_no_folder(self, config_model):
        with autotest.step("Patch global settings.agents: yandex_folder=None via model_construct"):
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

        with autotest.step("Act + Assert: _build_model raises ValueError, restore providers after"):
            try:
                with autotest.step("_build_model should raise ValueError"):
                    agent = _Dummy(config_model)
                    with pytest.raises(ValueError, match="yandex_folder required"):
                        agent._build_model("yandex-gpt-5.1")
            finally:
                settings.agents.providers.update(original_providers)

    @autotest.num("406")
    @autotest.external_id("fdbc94b5-03b1-4868-8548-e4a4e6493b62")
    @autotest.name("BaseAgent: _build_model, base_url/headers/model-uri for yandex")
    def test_fdbc94b5_build_model_yandex_characterization(self, config_model):
        with autotest.step("Create _Dummy agent"):
            agent = _Dummy(config_model)

        with autotest.step("Call _build_model for yandex"):
            model = agent._build_model("yandex-gpt-5.1")

        with autotest.step("Assert base_url, x-folder-id header, client model_name"):
            assert_equal(
                str(model.client.base_url),
                "https://ai.api.cloud.yandex.net/v1/",
                "base_url, default yandex endpoint",
            )
            assert_equal(
                model.client._custom_headers.get("x-folder-id"),
                "test-folder",
                "x-folder-id passed through to headers",
            )
            assert_equal(
                model.model_name,
                "gpt://test-folder/yandexgpt/latest",
                "model_name, gpt:// URI",
            )

    @autotest.num("407")
    @autotest.external_id("74ebaf3a-6499-46e6-8b98-a5d950bb8673")
    @autotest.name(
        "BaseAgent: _build_model, base_url/headers/model-uri for an openai-compatible model"
    )
    def test_74ebaf3a_build_model_openai_compatible_characterization(self, config_model):
        with autotest.step("Arrange: import config types"):
            from config.config_model import LlmProvider, ModelEntry, ProviderCreds
            from config.env_config_loader import settings

        with autotest.step("Register an openrouter provider and model in the global catalog"):
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

        with autotest.step(
            "Act + Assert: build model, assert client config, restore catalog after"
        ):
            try:
                with autotest.step("Create _Dummy agent and call _build_model"):
                    agent = _Dummy(config_model)
                    model = agent._build_model("openrouter-test-model")

                with autotest.step("Assert base_url, headers, api_key, client model_name"):
                    assert_equal(
                        str(model.client.base_url),
                        "https://openrouter.ai/api/v1/",
                        "base_url, from ProviderCreds",
                    )
                    assert_equal(
                        model.client._custom_headers.get("X-Title"),
                        "onlinetlabs",
                        "extra_headers passed through",
                    )
                    assert_equal(model.client.api_key, "sk-or-test", "api_key, from ProviderCreds")
                    assert_equal(
                        model.model_name,
                        "some-vendor/some-model",
                        "model_name, catalog slug",
                    )
            finally:
                settings.agents.providers.clear()
                settings.agents.providers.update(original_providers)
                settings.agents.catalog[:] = original_catalog

    @autotest.num("408")
    @autotest.external_id("8dc27f60-fe66-4195-a58e-8c96dc39588b")
    @autotest.name(
        "BaseAgent: without caching, two calls with different model_id each use their own model"
    )
    def test_8dc27f60_agent_for_no_cache_picks_right_model_per_call(self, config_model):
        with autotest.step("Arrange: import config types"):
            from config.config_model import LlmProvider, ModelEntry, ProviderCreds
            from config.env_config_loader import settings

        with autotest.step("Register a second provider/model in the global catalog"):
            creds = ProviderCreds(
                provider=LlmProvider.OPENAI,
                api_key="sk-second",
                base_url="https://openrouter.ai/api/v1",
            )
            entry = ModelEntry(
                id="second-model",
                label="second",
                provider_ref="second-provider",
                model="vendor/second-model",
            )
            original_providers = settings.agents.providers.copy()
            original_catalog = list(settings.agents.catalog)
            settings.agents.providers["second-provider"] = creds
            settings.agents.catalog.append(entry)

        with autotest.step("Act + Assert: call _agent_for twice, assert models, restore after"):
            try:
                with autotest.step("Create _Dummy agent and call _agent_for for two model_ids"):
                    agent = _Dummy(config_model)
                    agent1 = agent._agent_for("yandex-gpt-5.1", "en")
                    agent2 = agent._agent_for("second-model", "en")

                with autotest.step("Each call gives a fresh Agent with the right model"):
                    assert_true(agent1 is not agent2, "different Agent instances, no cache")
                    assert_equal(
                        agent1.model.model_name,
                        "gpt://test-folder/yandexgpt/latest",
                        "first model_id → yandex uri",
                    )
                    assert_equal(
                        agent2.model.model_name,
                        "vendor/second-model",
                        "second model_id → its own model_uri",
                    )
            finally:
                settings.agents.providers.clear()
                settings.agents.providers.update(original_providers)
                settings.agents.catalog[:] = original_catalog

    @autotest.num("403")
    @autotest.external_id("201db06b-9f48-4415-959a-0afe0c63842a")
    @autotest.name("BaseAgent: system_prompt raises NotImplementedError")
    def test_201db06b_system_prompt_raises(self, config_model):
        with autotest.step("Create BaseAgent"):
            agent = BaseAgent(config_model)

        with autotest.step("Call system_prompt"), pytest.raises(NotImplementedError):
            agent.system_prompt("en")

    @autotest.num("404")
    @autotest.external_id("2aaa5fea-ec64-41a1-b524-e5abb2cc168f")
    @autotest.name("BaseAgent: run raises NotImplementedError")
    async def test_2aaa5fea_run_raises(self, config_model):
        with autotest.step("Create BaseAgent"):
            agent = BaseAgent(config_model)

        with autotest.step("Call run"), pytest.raises(NotImplementedError):
            await agent.run(None)
