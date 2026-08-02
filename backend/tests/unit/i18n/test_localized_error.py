import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from i18n.errors import LocalizedError, localized_error_handler

pytestmark = [pytest.mark.unit]


def _client() -> TestClient:
    """App exposing one route that always raises a parameterised LocalizedError."""
    app = FastAPI()
    app.add_exception_handler(LocalizedError, localized_error_handler)

    @app.get("/boom")
    async def boom():
        raise LocalizedError("error.session.limit_reached", status_code=400, max=3)

    return TestClient(app)


class TestLocalizedError:
    @autotest.num("3120")
    @autotest.external_id("5ecd15a8-2448-426e-9418-79b436b31b42")
    @autotest.name("LocalizedError: the same failure renders per X-Locale")
    def test_5ecd15a8_detail_follows_locale(self):
        with autotest.step("Act: hit the failing route in both locales"):
            client = _client()
            en = client.get("/boom", headers={"X-Locale": "en"}).json()
            ru = client.get("/boom", headers={"X-Locale": "ru"}).json()

        with autotest.step("Assert: details differ, both interpolate the parameter"):
            assert_true(en["detail"] != ru["detail"], "detail is translated")
            assert_true(
                "3" in en["detail"] and "3" in ru["detail"], "the parameter is interpolated"
            )

    @autotest.num("3121")
    @autotest.external_id("a2e5086a-20ff-4e8a-b0d9-11dbf3a32034")
    @autotest.name("LocalizedError: the machine-readable code is locale-invariant")
    def test_a2e5086a_code_is_stable(self):
        with autotest.step("Act: hit the failing route in both locales"):
            client = _client()
            en = client.get("/boom", headers={"X-Locale": "en"}).json()
            ru = client.get("/boom", headers={"X-Locale": "ru"}).json()

        with autotest.step("Assert: both carry the same code and status"):
            assert_equal(en["code"], "error.session.limit_reached", "code is the catalog key")
            assert_equal(ru["code"], en["code"], "code does not vary by locale")

    @autotest.num("3122")
    @autotest.external_id("822302b9-b934-4c7f-9d06-5b58cb3ae412")
    @autotest.name("LocalizedError: status_code reaches the response, absent header falls back")
    def test_822302b9_status_and_fallback(self):
        with autotest.step("Act: hit the failing route without a locale header"):
            response = _client().get("/boom")

        with autotest.step("Assert: the declared status is used and the default locale renders"):
            assert_equal(response.status_code, 400, "status_code is honoured")
            assert_true(bool(response.json()["detail"]), "a detail is rendered without a header")
