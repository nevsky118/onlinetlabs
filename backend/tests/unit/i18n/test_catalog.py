import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from i18n import DEFAULT_LOCALE, t, validate_catalogs
from i18n import catalog as catalog_module

pytestmark = [pytest.mark.unit]


class TestTranslate:
    @autotest.num("3105")
    @autotest.external_id("09e0228b-5aa5-44ac-8d58-31adb986bf2d")
    @autotest.name("t: returns the message for the requested locale")
    def test_09e0228b_per_locale_lookup(self):
        with autotest.step("Act: look up one key in both locales"):
            en = t("error.user.not_found", "en")
            ru = t("error.user.not_found", "ru")

        with autotest.step("Assert: both are non-empty and differ"):
            assert_true(bool(en) and bool(ru), "both locales resolve the key")
            assert_true(en != ru, "the locales carry different text")

    @autotest.num("3106")
    @autotest.external_id("857f5ac7-cd11-44a0-99c5-4747f583a50c")
    @autotest.name("t: interpolates parameters")
    def test_857f5ac7_interpolation(self):
        with autotest.step("Act: render a parameterised key"):
            message = t("error.session.limit_reached", "en", max=3)

        with autotest.step("Assert: the parameter appears and no brace survives"):
            assert_true("3" in message, "the parameter is interpolated")
            assert_true("{" not in message, "no unrendered placeholder remains")

    @autotest.num("3107")
    @autotest.external_id("ecb73220-03b0-42f5-9f5c-33aaa3d16db4")
    @autotest.name("t: a key missing from the locale falls back to the default locale")
    def test_ecb73220_fallback(self, monkeypatch):
        with autotest.step("Arrange: a ru catalog that lacks a key the en catalog has"):
            monkeypatch.setattr(
                catalog_module,
                "_catalog",
                lambda locale: {"only.in.en": "fallback"} if locale == DEFAULT_LOCALE else {},
            )

        with autotest.step("Act: request the key in ru"):
            message = t("only.in.en", "ru")

        with autotest.step("Assert: the default-locale text is returned"):
            assert_equal(message, "fallback", "missing keys fall back to the default locale")

    @autotest.num("3108")
    @autotest.external_id("e86b84ea-7815-48ef-aa8a-49b0d753cbeb")
    @autotest.name("t: a key missing everywhere raises KeyError")
    def test_e86b84ea_missing_key_raises(self):
        with autotest.step("Act and assert: an unknown key is loud, not silent"):
            with pytest.raises(KeyError):
                t("error.does.not.exist", "en")

    @autotest.num("3136")
    @autotest.external_id("edfacd50-6795-48a0-ac1a-176b83424735")
    @autotest.name("t: an empty message is served as-is, not treated as missing")
    def test_edfacd50_empty_message_is_not_missing(self, monkeypatch):
        with autotest.step("Arrange: en holds text for the key, ru holds an empty string"):
            monkeypatch.setattr(
                catalog_module,
                "_catalog",
                lambda locale: {"only.in.en": "fallback"}
                if locale == DEFAULT_LOCALE
                else {"only.in.en": ""},
            )

        with autotest.step("Act: request the key in ru"):
            message = t("only.in.en", "ru")

        with autotest.step("Assert: the deliberate empty string is returned, not the en fallback"):
            assert_equal(message, "", "an empty message is not treated as missing")


class TestValidateCatalogs:
    @autotest.num("3109")
    @autotest.external_id("4e002124-789f-4a27-8c5b-3f19f5a68c3d")
    @autotest.name("validate_catalogs: the shipped catalogs pass")
    def test_4e002124_shipped_catalogs_valid(self):
        with autotest.step("Act and assert: validation of the real catalogs does not raise"):
            validate_catalogs()

    @autotest.num("3110")
    @autotest.external_id("fbe58164-2bfb-4ec3-b83e-3db9e50e4e6b")
    @autotest.name("validate_catalogs: key-set and placeholder mismatches raise")
    def test_fbe58164_mismatch_raises(self, monkeypatch):
        with autotest.step("Arrange: a catalog pair missing a key in ru"):
            monkeypatch.setattr(
                catalog_module,
                "_catalog",
                lambda locale: {"a": "x", "b": "y"} if locale == DEFAULT_LOCALE else {"a": "x"},
            )

        with autotest.step("Assert: the missing key raises"):
            with pytest.raises(ValueError):
                validate_catalogs()

        with autotest.step("Arrange: a catalog pair whose placeholders disagree"):
            monkeypatch.setattr(
                catalog_module,
                "_catalog",
                lambda locale: {"a": "{max} left"}
                if locale == DEFAULT_LOCALE
                else {"a": "{limit} left"},
            )

        with autotest.step("Assert: the placeholder mismatch raises"):
            with pytest.raises(ValueError):
                validate_catalogs()
