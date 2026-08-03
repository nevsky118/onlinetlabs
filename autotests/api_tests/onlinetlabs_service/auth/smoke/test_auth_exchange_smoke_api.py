# Smoke test for POST /auth/exchange over HTTP.

import pytest

from autotests.api.api_methods.onlinetlabs_service.auth_api import AuthApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import (
    assert_is_not_none,
    assert_equal,
)
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestAuthExchangeSmokeApi:
    """Smoke test for POST /auth/exchange."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.auth_api = AuthApi(anon_client, config)
        self.config = config

    @autotest.num("1")
    @autotest.external_id("28bb1710-997c-48c4-8642-7a00579279b2")
    @autotest.name("Smoke: POST /auth/exchange — 200 and JWT token in response")
    async def test_28bb1710_exchange_token(self):
        """Exchange of credentials -> JWT token."""
        # Arrange
        with autotest.step("Build exchange payload for the registered account"):
            account = self.config.accounts[ConstantsSettings.REGISTERED_ACCOUNT]
            exchange_data = {"user_id": account.sub, "email": account.email}

        # Act
        with autotest.step("Send POST /auth/exchange"):
            response = await self.auth_api.post_exchange(data=exchange_data)

        # Assert
        with autotest.step("Verify status code 200"):
            check_response_status(response, 200)

        with autotest.step("Verify access_token present and type bearer"):
            body = response.json()
            assert_is_not_none(body.get("access_token"), "access_token must not be None")
            assert_equal(body["token_type"], "bearer",
                         f"token_type: expected bearer, got {body['token_type']}")
