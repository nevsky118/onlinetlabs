import pytest
from mcp_sdk.testing import autotest

from config.config_model import ModelEntry
from config.llm_catalog import default_catalog

pytestmark = [pytest.mark.unit]


@autotest.num("1730")
@autotest.external_id("7646757f-c563-4116-879c-ea34b32144e4")
@autotest.name("default_catalog: содержит yandex и openrouter модели")
def test_7646757f_has_yandex_and_openrouter():
    with autotest.step("Получаем каталог"):
        cat = default_catalog()
    with autotest.step("Проверяем наличие ключевых id"):
        ids = {m.id for m in cat}
        assert "yandex-gpt-5.1" in ids
        assert "claude-opus-4.8" in ids
        assert all(isinstance(m, ModelEntry) for m in cat)


@autotest.num("1731")
@autotest.external_id("a31f27c3-2c8a-4f4e-b7d6-1388440f0c93")
@autotest.name("default_catalog: все provider_ref из разрешённого набора")
def test_a31f27c3_provider_refs():
    with autotest.step("Получаем provider_ref из каталога"):
        refs = {m.provider_ref for m in default_catalog()}
    with autotest.step("Проверяем допустимые провайдеры"):
        assert refs <= {"yandex", "openrouter"}
