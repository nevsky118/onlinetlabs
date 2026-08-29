import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from starlette.requests import Request

from i18n import DEFAULT_LOCALE, LOCALES, negotiate
from kit.deps import get_locale

pytestmark = [pytest.mark.unit]


def _request(locale_header: str | None) -> Request:
    """Minimal ASGI Request carrying an optional X-Locale header."""
    headers = [] if locale_header is None else [(b"x-locale", locale_header.encode())]
    return Request({"type": "http", "headers": headers, "client": ("10.0.0.1", 0), "state": {}})


class TestNegotiate:
    @autotest.num("3100")
    @autotest.external_id("bd909ecd-68dc-4ff7-8bf1-f5cf5dee418f")
    @autotest.name("negotiate: supported tags map to themselves")
    def test_bd909ecd_supported_tags(self):
        with autotest.step("Act: negotiate each supported locale"):
            results = [negotiate("en"), negotiate("ru")]

        with autotest.step("Assert: each tag maps to itself"):
            assert_equal(results, ["en", "ru"], "supported tags are returned unchanged")

    @autotest.num("3101")
    @autotest.external_id("7a687da8-5fad-488e-a0e1-82fbacf25b04")
    @autotest.name("negotiate: region subtag and case are normalised")
    def test_7a687da8_normalisation(self):
        with autotest.step("Act: negotiate region-qualified and upper-case tags"):
            results = [negotiate("ru-RU"), negotiate("EN"), negotiate("ru-RU,ru;q=0.9")]

        with autotest.step("Assert: all normalise to the base locale"):
            assert_equal(results, ["ru", "en", "ru"], "subtag stripped, case folded")

    @autotest.num("3102")
    @autotest.external_id("feab0d42-817d-4168-892c-dfe7dd4eee5c")
    @autotest.name("negotiate: unknown, empty and absent fall back to the default")
    def test_feab0d42_fallback(self):
        with autotest.step("Act: negotiate unsupported input"):
            results = [negotiate("de"), negotiate(""), negotiate(None), negotiate("   ")]

        with autotest.step("Assert: every case yields DEFAULT_LOCALE"):
            assert_equal(results, [DEFAULT_LOCALE] * 4, "unsupported input falls back")

    @autotest.num("3103")
    @autotest.external_id("52695bce-3a04-4388-a30b-f05f3d5519bd")
    @autotest.name("get_locale: reads X-Locale, defaults when the header is absent")
    def test_52695bce_get_locale_dependency(self):
        with autotest.step("Act: resolve locale from two requests"):
            with_header = get_locale(_request("ru"))
            without_header = get_locale(_request(None))

        with autotest.step("Assert: header wins, absence falls back"):
            assert_equal(with_header, "ru", "X-Locale header is honoured")
            assert_equal(without_header, DEFAULT_LOCALE, "absent header falls back")

    @autotest.num("3104")
    @autotest.external_id("ce0b8a5c-6b6e-44e4-80da-9bbe10c1add0")
    @autotest.name("locale constants: DEFAULT_LOCALE is a member of LOCALES")
    def test_ce0b8a5c_constants_agree(self):
        with autotest.step("Assert: the default is a supported locale"):
            assert_equal(DEFAULT_LOCALE in LOCALES, True, "the default is a supported locale")
