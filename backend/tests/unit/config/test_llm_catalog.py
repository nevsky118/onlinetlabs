import pytest
from mcp_sdk.testing import autotest

from config.config_model import ModelEntry
from config.llm_catalog import default_catalog

pytestmark = [pytest.mark.unit]


@autotest.num("2602")
@autotest.external_id("7646757f-c563-4116-879c-ea34b32144e4")
@autotest.name("default_catalog: contains yandex and openrouter models")
def test_7646757f_has_yandex_and_openrouter():
    with autotest.step("Get the catalog"):
        cat = default_catalog()
    with autotest.step("Check key ids are present"):
        ids = {m.id for m in cat}
        assert "yandex-gpt-5.1" in ids
        assert "claude-opus-4.8" in ids
        assert all(isinstance(m, ModelEntry) for m in cat)


@autotest.num("2603")
@autotest.external_id("a31f27c3-2c8a-4f4e-b7d6-1388440f0c93")
@autotest.name("default_catalog: all provider_ref values are in the allowed set")
def test_a31f27c3_provider_refs():
    with autotest.step("Get provider_ref values from the catalog"):
        refs = {m.provider_ref for m in default_catalog()}
    with autotest.step("Check allowed providers"):
        assert refs <= {"yandex", "openrouter"}
