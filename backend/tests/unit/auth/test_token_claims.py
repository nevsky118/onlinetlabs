import pytest
from mcp_sdk.testing import autotest

from auth.dependencies import create_backend_token, decode_backend_token
from config import settings

pytestmark = [pytest.mark.unit, pytest.mark.auth]


@autotest.name("create_backend_token: can_select=True кладётся в payload")
def test_token_carries_can_select():
    tok = create_backend_token("u1", "student", can_select=True)
    payload = decode_backend_token(tok, settings.api.jwt_secret)
    assert payload["can_select"] is True
    assert payload["sub"] == "u1"


@autotest.name("create_backend_token: can_select по умолчанию False")
def test_token_can_select_defaults_false():
    tok = create_backend_token("u2", "instructor")
    payload = decode_backend_token(tok, settings.api.jwt_secret)
    assert payload["can_select"] is False
