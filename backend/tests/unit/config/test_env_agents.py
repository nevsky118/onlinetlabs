import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_false,
    assert_in,
    assert_is_none,
    assert_is_not_none,
    assert_true,
)

from config.config_model import LlmProvider
from config.env_config_loader import build_agents_config

pytestmark = [pytest.mark.unit]


class TestEnvAgents:
    @autotest.num("210")
    @autotest.external_id("19f2f06a-c71f-4cc2-ad1d-1991dc0b2366")
    @autotest.name("build_agents_config: new env keys, both providers")
    def test_19f2f06a_build_agents_from_new_env(self):
        with autotest.step("Build a config from an env dict"):
            cfg = build_agents_config(
                {
                    "YANDEX_API_KEY": "yk",
                    "YANDEX_FOLDER": "fld",
                    "OPENROUTER_API_KEY": "ork",
                    "AGENTS_CHAT_MODEL": "yandex-gpt-5.1",
                    "AGENTS_INTERVENTION_MODEL": "yandex-gpt-5.1",
                }
            )
        with autotest.step("Check providers and catalog"):
            assert_equal(set(cfg.providers), {"yandex", "openrouter"}, "providers")
            assert_equal(
                cfg.providers["openrouter"].provider,
                LlmProvider.OPENAI,
                "provider",
            )
            assert_is_not_none(cfg.get_entry("claude-opus-4.8"), "get entry")

    @autotest.num("211")
    @autotest.external_id("b8b87ba4-04cd-4c32-b369-0859bb3f5f7e")
    @autotest.name("build_agents_config: without an openrouter key, models are filtered")
    def test_b8b87ba4_openrouter_models_filtered_when_no_key(self):
        with autotest.step("Build a config without OPENROUTER_API_KEY"):
            cfg = build_agents_config(
                {
                    "YANDEX_API_KEY": "yk",
                    "YANDEX_FOLDER": "fld",
                    "AGENTS_CHAT_MODEL": "yandex-gpt-5.1",
                    "AGENTS_INTERVENTION_MODEL": "yandex-gpt-5.1",
                }
            )
        with autotest.step("Check the catalog filtering"):
            assert_false("openrouter" in cfg.providers, "'openrouter' absent")
            assert_is_none(cfg.get_entry("claude-opus-4.8"), "get entry")
            assert_is_not_none(cfg.get_entry("yandex-gpt-5.1"), "get entry")

    @autotest.num("213")
    @autotest.external_id("e7a24847-3394-464b-ba0c-a54237a4d0ea")
    @autotest.name(
        "build_agents_config: openrouter-only, default yandex-gpt-5.1 → falls back to the first catalog entry"
    )
    def test_e7a24847_openrouter_only_fallback_when_default_model_missing(self):
        with autotest.step("Build a config with only OPENROUTER_API_KEY, AGENTS_CHAT_MODEL unset"):
            cfg = build_agents_config(
                {
                    "OPENROUTER_API_KEY": "ork",
                }
            )
        with autotest.step(
            "chat_model and intervention_model are openrouter models from the catalog"
        ):
            assert_in(
                cfg.chat_model,
                {entryntry_2ntry_3.id for entryntry_2ntry_3 in cfg.catalog},
                "chat model",
            )
            assert_in(
                cfg.intervention_model,
                {entryntry_2ntry_3.id for entryntry_2ntry_3 in cfg.catalog},
                "intervention model",
            )
            assert_true(
                all(
                    entryntry_2ntry_3.provider_ref == "openrouter"
                    for entryntry_2ntry_3 in cfg.catalog
                ),
                "every catalog entry is openrouter",
            )

    @autotest.num("212")
    @autotest.external_id("8382ecb4-4b02-409f-8dc4-b481208dc350")
    @autotest.name("build_agents_config: back-compat AGENTS_PROVIDER")
    def test_8382ecb4_back_compat_old_agents_env(self):
        with autotest.step("Build a config through the old AGENTS_* variables"):
            cfg = build_agents_config(
                {
                    "AGENTS_PROVIDER": "yandex",
                    "AGENTS_MODEL": "yandexgpt/latest",
                    "AGENTS_API_KEY": "yk",
                    "AGENTS_YANDEX_FOLDER": "fld",
                }
            )
        with autotest.step("Check the result"):
            assert_in("yandex", cfg.providers, "yandex provider")
            assert_is_not_none(cfg.get_entry(cfg.chat_model), "get entry")
