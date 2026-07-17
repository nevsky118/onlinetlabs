import pytest
from mcp_sdk.testing import autotest

from config.config_model import LlmProvider
from config.env_config_loader import build_agents_config

pytestmark = [pytest.mark.unit]


@autotest.num("210")
@autotest.external_id("19f2f06a-c71f-4cc2-ad1d-1991dc0b2366")
@autotest.name("build_agents_config: новые env-ключи, оба провайдера")
def test_19f2f06a_build_agents_from_new_env():
    with autotest.step("Собираем конфиг из env-словаря"):
        cfg = build_agents_config(
            {
                "YANDEX_API_KEY": "yk",
                "YANDEX_FOLDER": "fld",
                "OPENROUTER_API_KEY": "ork",
                "AGENTS_CHAT_MODEL": "yandex-gpt-5.1",
                "AGENTS_INTERVENTION_MODEL": "yandex-gpt-5.1",
            }
        )
    with autotest.step("Проверяем провайдеры и каталог"):
        assert set(cfg.providers) == {"yandex", "openrouter"}
        assert cfg.providers["openrouter"].provider == LlmProvider.OPENAI
        assert cfg.get_entry("claude-opus-4.8") is not None


@autotest.num("211")
@autotest.external_id("b8b87ba4-04cd-4c32-b369-0859bb3f5f7e")
@autotest.name("build_agents_config: без openrouter-ключа фильтрует модели")
def test_b8b87ba4_openrouter_models_filtered_when_no_key():
    with autotest.step("Собираем конфиг без OPENROUTER_API_KEY"):
        cfg = build_agents_config(
            {
                "YANDEX_API_KEY": "yk",
                "YANDEX_FOLDER": "fld",
                "AGENTS_CHAT_MODEL": "yandex-gpt-5.1",
                "AGENTS_INTERVENTION_MODEL": "yandex-gpt-5.1",
            }
        )
    with autotest.step("Проверяем фильтрацию каталога"):
        assert "openrouter" not in cfg.providers
        assert cfg.get_entry("claude-opus-4.8") is None
        assert cfg.get_entry("yandex-gpt-5.1") is not None


@autotest.num("213")
@autotest.external_id("e7a24847-3394-464b-ba0c-a54237a4d0ea")
@autotest.name(
    "build_agents_config: openrouter-only, дефолт yandex-gpt-5.1 → fallback на первый catalog entry"
)
def test_e7a24847_openrouter_only_fallback_when_default_model_missing():
    with autotest.step("Собираем конфиг только с OPENROUTER_API_KEY, AGENTS_CHAT_MODEL не задан"):
        cfg = build_agents_config(
            {
                "OPENROUTER_API_KEY": "ork",
            }
        )
    with autotest.step("chat_model и intervention_model — openrouter-модели из каталога"):
        assert cfg.chat_model in {m.id for m in cfg.catalog}
        assert cfg.intervention_model in {m.id for m in cfg.catalog}
        assert all(m.provider_ref == "openrouter" for m in cfg.catalog)


@autotest.num("212")
@autotest.external_id("8382ecb4-4b02-409f-8dc4-b481208dc350")
@autotest.name("build_agents_config: back-compat AGENTS_PROVIDER")
def test_8382ecb4_back_compat_old_agents_env():
    with autotest.step("Собираем конфиг через старые AGENTS_* переменные"):
        cfg = build_agents_config(
            {
                "AGENTS_PROVIDER": "yandex",
                "AGENTS_MODEL": "yandexgpt/latest",
                "AGENTS_API_KEY": "yk",
                "AGENTS_YANDEX_FOLDER": "fld",
            }
        )
    with autotest.step("Проверяем результат"):
        assert "yandex" in cfg.providers
        assert cfg.get_entry(cfg.chat_model) is not None
