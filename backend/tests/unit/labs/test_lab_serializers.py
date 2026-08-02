import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from labs.serializers import to_lab_response
from models.lab import Lab

pytestmark = [pytest.mark.unit]


def _lab(**overrides) -> Lab:
    """Detached Lab row with localized content."""
    defaults = dict(
        slug="lan-static-ip",
        title_i18n={"en": "Static IP", "ru": "Статический IP"},
        description_i18n={"en": "Two hosts", "ru": "Два хоста"},
        difficulty="beginner",
        course_slug="networking",
        environment_type="gns3",
        order_in_course=1,
        meta=None,
    )
    return Lab(**(defaults | overrides))


class TestToLabResponse:
    @autotest.num("3117")
    @autotest.external_id("bf54d8dc-3a83-402a-b546-a9a711a78edc")
    @autotest.name("to_lab_response: renders title and description in the requested locale")
    def test_bf54d8dc_renders_requested_locale(self):
        with autotest.step("Act: serialize the same lab in both locales"):
            en = to_lab_response(_lab(), "en")
            ru = to_lab_response(_lab(), "ru")

        with autotest.step("Assert: each response carries its own locale's text"):
            assert_equal(en.title, "Static IP", "en title")
            assert_equal(ru.title, "Статический IP", "ru title")
            assert_equal(ru.description, "Два хоста", "ru description")

    @autotest.num("3118")
    @autotest.external_id("e0bd7845-7f49-4e95-9d87-54258e7208ad")
    @autotest.name("to_lab_response: an untranslated lab falls back instead of failing")
    def test_e0bd7845_untranslated_falls_back(self):
        with autotest.step("Act: serialize a lab that has only English content"):
            response = to_lab_response(
                _lab(title_i18n={"en": "Static IP"}, description_i18n=None), "ru"
            )

        with autotest.step("Assert: the English text is served and the absent description is None"):
            assert_equal(response.title, "Static IP", "falls back to the default locale")
            assert_equal(
                response.description, None, "an absent description stays None, not empty string"
            )

    @autotest.num("3119")
    @autotest.external_id("36f071ae-a148-431e-a1a9-eaa7d7f1cb47")
    @autotest.name("to_lab_response: non-content fields pass through untouched")
    def test_36f071ae_passthrough_fields(self):
        with autotest.step("Act: serialize a lab"):
            response = to_lab_response(_lab(), "en")

        with autotest.step("Assert: identifiers and metadata are unchanged"):
            assert_equal(response.slug, "lan-static-ip", "slug")
            assert_equal(response.environment_type, "gns3", "environment_type")
            assert_equal(response.order_in_course, 1, "order_in_course")
