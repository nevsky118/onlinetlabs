import pytest

from config.env_config_loader import build_agents_config
from config.config_model import LlmProvider
from mcp_sdk.testing import autotest

pytestmark = [pytest.mark.unit]


@autotest.num("210")
@autotest.external_id("c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f")
@autotest.name("build_agents_config: новые env-ключи, оба провайдера")
def test_build_agents_from_new_env():
    with autotest.step("Собираем конфиг из env-словаря"):
        cfg = build_agents_config({
            "YANDEX_API_KEY": "yk", "YANDEX_FOLDER": "fld",
            "OPENROUTER_API_KEY": "ork",
            "AGENTS_CHAT_MODEL": "yandex-gpt-5.1",
            "AGENTS_INTERVENTION_MODEL": "yandex-gpt-5.1",
        })
    with autotest.step("Проверяем провайдеры и каталог"):
        assert set(cfg.providers) == {"yandex", "openrouter"}
        assert cfg.providers["openrouter"].provider == LlmProvider.OPENAI
        assert cfg.get_entry("claude-opus-4.8") is not None


@autotest.num("211")
@autotest.external_id("d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a")
@autotest.name("build_agents_config: без openrouter-ключа фильтрует модели")
def test_openrouter_models_filtered_when_no_key():
    with autotest.step("Собираем конфиг без OPENROUTER_API_KEY"):
        cfg = build_agents_config({
            "YANDEX_API_KEY": "yk", "YANDEX_FOLDER": "fld",
            "AGENTS_CHAT_MODEL": "yandex-gpt-5.1",
            "AGENTS_INTERVENTION_MODEL": "yandex-gpt-5.1",
        })
    with autotest.step("Проверяем фильтрацию каталога"):
        assert "openrouter" not in cfg.providers
        assert cfg.get_entry("claude-opus-4.8") is None
        assert cfg.get_entry("yandex-gpt-5.1") is not None


@autotest.num("213")
@autotest.external_id("f6a7b8c9-d0e1-4f2a-3b4c-5d6e7f8a9b0c")
@autotest.name("build_agents_config: openrouter-only, дефолт yandex-gpt-5.1 → fallback на первый catalog entry")
def test_openrouter_only_fallback_when_default_model_missing():
    with autotest.step("Собираем конфиг только с OPENROUTER_API_KEY, AGENTS_CHAT_MODEL не задан"):
        cfg = build_agents_config({
            "OPENROUTER_API_KEY": "ork",
        })
    with autotest.step("chat_model и intervention_model — openrouter-модели из каталога"):
        assert cfg.chat_model in {m.id for m in cfg.catalog}
        assert cfg.intervention_model in {m.id for m in cfg.catalog}
        assert all(m.provider_ref == "openrouter" for m in cfg.catalog)


@autotest.num("212")
@autotest.external_id("e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b")
@autotest.name("build_agents_config: back-compat AGENTS_PROVIDER")
def test_back_compat_old_agents_env():
    with autotest.step("Собираем конфиг через старые AGENTS_* переменные"):
        cfg = build_agents_config({
            "AGENTS_PROVIDER": "yandex", "AGENTS_MODEL": "yandexgpt/latest",
            "AGENTS_API_KEY": "yk", "AGENTS_YANDEX_FOLDER": "fld",
        })
    with autotest.step("Проверяем результат"):
        assert "yandex" in cfg.providers
        assert cfg.get_entry(cfg.chat_model) is not None
