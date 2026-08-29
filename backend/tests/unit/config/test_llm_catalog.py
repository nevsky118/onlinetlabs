import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_in, assert_less_equal, assert_true

from config.config_model import ModelEntry
from config.llm_catalog import default_catalog

pytestmark = [pytest.mark.unit]


class TestLlmCatalog:
    @autotest.num("2602")
    @autotest.external_id("7646757f-c563-4116-879c-ea34b32144e4")
    @autotest.name("default_catalog: contains yandex and openrouter models")
    def test_7646757f_has_yandex_and_openrouter(self):
        with autotest.step("Get the catalog"):
            cat = default_catalog()
        with autotest.step("Check key ids are present"):
            ids = {itemtem_2.id for itemtem_2 in cat}
            assert_in("yandex-gpt-5.1", ids, "yandex model")
            assert_in("claude-opus-4.8", ids, "openrouter model")
            assert_true(
                all(isinstance(itemtem_2, ModelEntry) for itemtem_2 in cat),
                "all",
            )

    @autotest.num("2603")
    @autotest.external_id("a31f27c3-2c8a-4f4e-b7d6-1388440f0c93")
    @autotest.name("default_catalog: all provider_ref values are in the allowed set")
    def test_a31f27c3_provider_refs(self):
        with autotest.step("Get provider_ref values from the catalog"):
            refs = {entry.provider_ref for entry in default_catalog()}
        with autotest.step("Check allowed providers"):
            assert_less_equal(refs, {"yandex", "openrouter"}, "only known providers")
