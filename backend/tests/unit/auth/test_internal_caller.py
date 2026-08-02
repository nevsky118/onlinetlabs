import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none

from auth.dependencies import require_internal_caller
from config import settings

pytestmark = [pytest.mark.unit, pytest.mark.auth]


class TestRequireInternalCaller:
    @autotest.num("2430")
    @autotest.external_id("282c7c42-5ad5-4f03-aee9-0b73aa5ebcdd")
    @autotest.name("require_internal_caller: correct token → passes without exception")
    def test_282c7c42_correct_token_passes(self, monkeypatch):
        with autotest.step("Arrange: configure internal_api_token and matching credentials"):
            monkeypatch.setattr(settings.security, "internal_api_token", "right-token")
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="right-token")

        with autotest.step("Act: call the dependency directly"):
            result = require_internal_caller(credentials=creds)

        with autotest.step("Assert: returns None, no exception raised"):
            assert_is_none(result, "require_internal_caller returns None")

    @autotest.num("2431")
    @autotest.external_id("1c5fb6cc-cd2a-4041-8624-6fa536a3c4af")
    @autotest.name("require_internal_caller: wrong token → HTTPException 401")
    def test_1c5fb6cc_wrong_token_raises_401(self, monkeypatch):
        with autotest.step("Arrange: configure internal_api_token, credentials don't match"):
            monkeypatch.setattr(settings.security, "internal_api_token", "right-token")
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong")

        with autotest.step("Act + Assert: expect 401"):
            with pytest.raises(HTTPException) as exc_info:
                require_internal_caller(credentials=creds)
            assert_equal(exc_info.value.status_code, 401, "status_code = 401")

    @autotest.num("2432")
    @autotest.external_id("d815a905-e342-47b2-92b7-aab576743b79")
    @autotest.name(
        "require_internal_caller: empty internal_api_token → HTTPException 401 for any token"
    )
    def test_d815a905_empty_configured_token_raises_401(self, monkeypatch):
        with autotest.step("Arrange: internal_api_token empty, presented token non-empty"):
            monkeypatch.setattr(settings.security, "internal_api_token", "")
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="anything")

        with autotest.step("Act + Assert: expect 401 via the not-expected guard"):
            with pytest.raises(HTTPException) as exc_info:
                require_internal_caller(credentials=creds)
            assert_equal(exc_info.value.status_code, 401, "status_code = 401")
