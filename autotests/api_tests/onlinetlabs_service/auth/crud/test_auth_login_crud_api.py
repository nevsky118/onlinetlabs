# CRUD-тесты POST /auth/login.

import pytest

from autotests.api.api_helpers.onlinetlabs_service.auth_helper_api import AuthHelperApi
from autotests.api.api_methods.onlinetlabs_service.auth_api import AuthApi
from autotests.api.data.onlinetlabs_service.auth_data_api import AuthRegisterData, AuthLoginData, valid_password
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestAuthLoginCrudApi:
    """CRUD-тесты POST /auth/login."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.auth_helper = AuthHelperApi(anon_client, config)
        self.auth_api = AuthApi(anon_client, config)

    @autotest.num("5")
    @autotest.external_id("e5f6a7b8-c9d0-1234-efab-345678901234")
    @autotest.name("Auth Login: success (200)")
    async def test_e5f6a7b8_login_success(self):
        """Успешный логин после регистрации возвращает 200."""
        # Arrange
        with autotest.step("Регистрируем пользователя"):
            reg_data = AuthRegisterData()
            await self.auth_helper.register_user(reg_data.data)

        login_data = {
            "email": reg_data.email,
            "password": reg_data.password,
        }

        # Act
        with autotest.step("Логинимся с корректными данными"):
            response = await self.auth_api.post_login(data=login_data)

        # Assert
        with autotest.step("Проверяем статус код 200"):
            check_response_status(response, 200)

    @autotest.num("6")
    @autotest.external_id("f6a7b8c9-d0e1-2345-fabc-456789012345")
    @autotest.name("Auth Login: wrong password (401)")
    async def test_f6a7b8c9_login_wrong_password(self):
        """Логин с неверным паролем возвращает 401."""
        # Arrange
        with autotest.step("Регистрируем пользователя"):
            reg_data = AuthRegisterData()
            await self.auth_helper.register_user(reg_data.data)

        login_data = {
            "email": reg_data.email,
            "password": valid_password(),
        }

        # Act
        with autotest.step("Логинимся с неверным паролем"):
            response = await self.auth_api.post_login(data=login_data)

        # Assert
        with autotest.step("Проверяем статус код 401"):
            check_response_status(response, 401)

    @autotest.num("7")
    @autotest.external_id("a7b8c9d0-e1f2-3456-abcd-567890123456")
    @autotest.name("Auth Login: non-existent email (401)")
    async def test_a7b8c9d0_login_nonexistent_email(self):
        """Логин с несуществующим email возвращает 401."""
        # Arrange
        login_data = AuthLoginData()

        # Act
        with autotest.step("Логинимся с несуществующим email"):
            response = await self.auth_api.post_login(data=login_data.data)

        # Assert
        with autotest.step("Проверяем статус код 401"):
            check_response_status(response, 401)
