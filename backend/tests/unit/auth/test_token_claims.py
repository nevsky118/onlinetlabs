import pytest
from mcp_sdk.testing import autotest

from auth.dependencies import create_backend_token, decode_backend_token
from config import settings

pytestmark = [pytest.mark.unit, pytest.mark.auth]


@autotest.num("3215")
@autotest.external_id("fb7e683f-ae1f-4a75-85ca-c2554859f8fc")
@autotest.name("create_backend_token: can_select=True lands in the payload")
def test_fb7e683f_token_carries_can_select():
    with autotest.step("Act: create a backend token with can_select=True"):
        tok = create_backend_token("u1", "student", can_select=True)

    with autotest.step("Act: decode it"):
        payload = decode_backend_token(tok, settings.api.jwt_secret)

    with autotest.step("Assert: payload carries can_select=True and the subject"):
        assert payload["can_select"] is True
        assert payload["sub"] == "u1"


@autotest.num("3216")
@autotest.external_id("af52fd47-0161-49b0-84da-fdb3f54fc796")
@autotest.name("create_backend_token: can_select defaults to False")
def test_af52fd47_token_can_select_defaults_false():
    with autotest.step("Act: create a backend token without can_select"):
        tok = create_backend_token("u2", "instructor")

    with autotest.step("Act: decode it"):
        payload = decode_backend_token(tok, settings.api.jwt_secret)

    with autotest.step("Assert: payload defaults can_select to False"):
        assert payload["can_select"] is False
