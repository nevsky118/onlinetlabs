import pytest

from config.llm_catalog import default_catalog
from config.config_model import ModelEntry
from mcp_sdk.testing import autotest

pytestmark = [pytest.mark.unit]


@autotest.num("200")
@autotest.external_id("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
@autotest.name("default_catalog: содержит yandex и openrouter модели")
def test_default_catalog_has_yandex_and_openrouter():
    with autotest.step("Получаем каталог"):
        cat = default_catalog()
    with autotest.step("Проверяем наличие ключевых id"):
        ids = {m.id for m in cat}
        assert "yandex-gpt-5.1" in ids
        assert "claude-opus-4.8" in ids
        assert all(isinstance(m, ModelEntry) for m in cat)


@autotest.num("201")
@autotest.external_id("b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e")
@autotest.name("default_catalog: все provider_ref из разрешённого набора")
def test_default_catalog_provider_refs():
    with autotest.step("Получаем provider_ref из каталога"):
        refs = {m.provider_ref for m in default_catalog()}
    with autotest.step("Проверяем допустимые провайдеры"):
        assert refs <= {"yandex", "openrouter"}
