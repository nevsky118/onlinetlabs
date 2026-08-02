import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from i18n import as_locale_map, resolve_localized

pytestmark = [pytest.mark.unit]


class TestResolveLocalized:
    @autotest.num("3111")
    @autotest.external_id("1f185254-e303-426e-af8c-d24c1db6401b")
    @autotest.name("resolve_localized: a plain string means the same text in every locale")
    def test_1f185254_plain_string(self):
        with autotest.step("Act: resolve a plain string in both locales"):
            results = [resolve_localized("PC1", "en"), resolve_localized("PC1", "ru")]

        with autotest.step("Assert: the string passes through unchanged"):
            assert_equal(results, ["PC1", "PC1"], "a plain string is locale-independent")

    @autotest.num("3112")
    @autotest.external_id("fdb685f8-16a5-435f-8cad-663d40960197")
    @autotest.name("resolve_localized: a locale map returns the requested locale")
    def test_fdb685f8_map_hit(self):
        with autotest.step("Act: resolve a fully populated map"):
            value = {"en": "Static IP", "ru": "Статический IP"}

        with autotest.step("Assert: each locale gets its own text"):
            assert_equal(resolve_localized(value, "en"), "Static IP", "en resolves to en")
            assert_equal(resolve_localized(value, "ru"), "Статический IP", "ru resolves to ru")

    @autotest.num("3113")
    @autotest.external_id("b7cfd103-b1db-4a5c-9cbd-124ce8d9a974")
    @autotest.name("resolve_localized: an untranslated map falls back to the default locale")
    def test_b7cfd103_map_fallback_to_default(self):
        with autotest.step("Act: resolve a map that has only the default locale"):
            result = resolve_localized({"en": "Static IP"}, "ru")

        with autotest.step("Assert: the default-locale text is returned"):
            assert_equal(result, "Static IP", "missing translations degrade to the default")

    @autotest.num("3114")
    @autotest.external_id("d614ba2e-9d3a-4b6a-bf26-c041b7811b19")
    @autotest.name("resolve_localized: a map without the default locale falls back to any value")
    def test_d614ba2e_map_fallback_to_any(self):
        with autotest.step(
            "Act: resolve a map that has neither the requested nor the default locale"
        ):
            result = resolve_localized({"ru": "Статический IP"}, "en")

        with autotest.step(
            "Assert: the only available text is returned rather than an empty string"
        ):
            assert_equal(result, "Статический IP", "any present value beats nothing")

    @autotest.num("3115")
    @autotest.external_id("697a6e31-aa13-40cf-b1ed-b31041cb0819")
    @autotest.name("resolve_localized: None and an empty map yield an empty string")
    def test_697a6e31_empty(self):
        with autotest.step("Act: resolve absent content"):
            results = [resolve_localized(None, "en"), resolve_localized({}, "en")]

        with autotest.step("Assert: both yield an empty string, never None"):
            assert_equal(results, ["", ""], "absent content is an empty string")


class TestAsLocaleMap:
    @autotest.num("3116")
    @autotest.external_id("f3af4dde-5977-41f9-a381-2b633b82ecc6")
    @autotest.name("as_locale_map: a bare string is stored under the default locale")
    def test_f3af4dde_normalises_input(self):
        with autotest.step("Act: normalise the three accepted input shapes"):
            from_string = as_locale_map("Static IP")
            from_map = as_locale_map({"en": "Static IP", "ru": ""})
            from_none = as_locale_map(None)

        with autotest.step(
            "Assert: strings are tagged, empty translations are dropped, None stays None"
        ):
            assert_equal(
                from_string, {"en": "Static IP"}, "a bare string becomes a default-locale map"
            )
            assert_equal(from_map, {"en": "Static IP"}, "empty translations are dropped")
            assert_equal(from_none, None, "None passes through")
