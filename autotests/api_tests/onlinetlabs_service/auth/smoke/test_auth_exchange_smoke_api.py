# Smoke-тест POST /auth/exchange через HTTP.

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
    """Smoke-тест POST /auth/exchange."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.auth_api = AuthApi(anon_client, config)
        self.config = config

    @autotest.num("1")
    @autotest.external_id("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    @autotest.name("Smoke: POST /auth/exchange — 200 и JWT-токен в ответе")
    async def test_a1b2c3d4_exchange_token(self):
        """Обмен учётных данных -> JWT токен."""
        # Arrange
        account = self.config.accounts[ConstantsSettings.REGISTERED_ACCOUNT]
        exchange_data = {"user_id": account.sub, "email": account.email}

        # Act
        with autotest.step("Отправляем POST /auth/exchange"):
            response = await self.auth_api.post_exchange(data=exchange_data)

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)

        body = response.json()
        with autotest.step("Проверяем наличие access_token и тип bearer"):
            assert_is_not_none(body.get("access_token"), "access_token не должен быть None")
            assert_equal(body["token_type"], "bearer",
                         f"token_type: ожидался bearer, получен {body['token_type']}")
