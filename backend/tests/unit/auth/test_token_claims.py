import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from auth.dependencies import create_backend_token, decode_backend_token
from config import settings

pytestmark = [pytest.mark.unit, pytest.mark.auth]


class TestTokenClaims:
    @autotest.num("3215")
    @autotest.external_id("fb7e683f-ae1f-4a75-85ca-c2554859f8fc")
    @autotest.name("create_backend_token: can_select=True lands in the payload")
    def test_fb7e683f_token_carries_can_select(self):
        with autotest.step("Act: create a backend token with can_select=True"):
            tok = create_backend_token("u1", "student", can_select=True)

        with autotest.step("Act: decode it"):
            payload = decode_backend_token(tok, settings.api.jwt_secret)

        with autotest.step("Assert: payload carries can_select=True and the subject"):
            assert_equal(payload["can_select"], True, "can select")
            assert_equal(payload["sub"], "u1", "sub")

    @autotest.num("3216")
    @autotest.external_id("af52fd47-0161-49b0-84da-fdb3f54fc796")
    @autotest.name("create_backend_token: can_select defaults to False")
    def test_af52fd47_token_can_select_defaults_false(self):
        with autotest.step("Act: create a backend token without can_select"):
            tok = create_backend_token("u2", "instructor")

        with autotest.step("Act: decode it"):
            payload = decode_backend_token(tok, settings.api.jwt_secret)

        with autotest.step("Assert: payload defaults can_select to False"):
            assert_equal(payload["can_select"], False, "can select")
