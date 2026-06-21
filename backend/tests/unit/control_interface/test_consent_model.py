import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none

from models.consent import Consent

pytestmark = [pytest.mark.unit]


class TestConsentModel:
    @autotest.num("1740")
    @autotest.external_id("bd3454ca-6bff-4d27-a239-3a95e7f44677")
    @autotest.name("Consent: модель study с полями observe/act")
    def test_bd3454ca_fields(self):
        with autotest.step("Act: создать study-согласие"):
            c = Consent(id="c1", user_id="u1", scope="study", observe=True, act=True)
        with autotest.step("Assert: поля заданы, не отозвано"):
            assert_equal(c.scope, "study", "scope")
            assert_equal(c.observe, True, "observe")
            assert_is_none(c.revoked_at, "не отозвано")
