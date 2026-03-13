# CRUD-тесты POST /auth/register.

import pytest

from autotests.api.api_helpers.onlinetlabs_service.auth_helper_api import AuthHelperApi
from autotests.api.api_methods.onlinetlabs_service.auth_api import AuthApi
from autotests.api.data.onlinetlabs_service.auth_data_api import AuthRegisterData, short_password
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status, verify_data


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestAuthRegisterCrudApi:
    """CRUD-тесты POST /auth/register."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.auth_helper = AuthHelperApi(anon_client, config)
        self.auth_api = AuthApi(anon_client, config)

    @autotest.num("2")
    @autotest.external_id("b2c3d4e5-f6a7-8901-bcde-f12345678901")
    @autotest.name("Auth Register: success (201)")
    async def test_b2c3d4e5_register_success(self):
        """Успешная регистрация возвращает 201 и корректные данные."""
        # Arrange
        reg_data = AuthRegisterData()

        # Act
        with autotest.step("Регистрируем нового пользователя"):
            response = await self.auth_api.post_register(data=reg_data.data)

        # Assert
        with autotest.step("Проверяем статус код 201"):
            check_response_status(response, 201)

        with autotest.step("Проверяем, что возвращённые данные совпадают с отправленными"):
            verify_data(
                actual_data=response.json(),
                expected_data=reg_data.data,
                verified_fields=["email", "name"],
            )

    @autotest.num("3")
    @autotest.external_id("c3d4e5f6-a7b8-9012-cdef-123456789012")
    @autotest.name("Auth Register: duplicate email (409)")
    async def test_c3d4e5f6_register_duplicate_email(self):
        """Регистрация с существующим email возвращает 409."""
        # Arrange
        with autotest.step("Регистрируем пользователя"):
            reg_data = AuthRegisterData()
            await self.auth_helper.register_user(reg_data.data)

        # Act
        with autotest.step("Повторная регистрация с тем же email"):
            response = await self.auth_api.post_register(data=reg_data.data)

        # Assert
        with autotest.step("Проверяем статус код 409"):
            check_response_status(response, 409)

    @autotest.num("4")
    @autotest.external_id("d4e5f6a7-b8c9-0123-defa-234567890123")
    @autotest.name("Auth Register: short password (422)")
    async def test_d4e5f6a7_register_short_password(self):
        """Пароль < 8 символов возвращает 422."""
        # Arrange
        reg_data = AuthRegisterData()
        reg_data.data["password"] = short_password()

        # Act
        with autotest.step("Регистрация с коротким паролем"):
            response = await self.auth_api.post_register(data=reg_data.data)

        # Assert
        with autotest.step("Проверяем статус код 422"):
            check_response_status(response, 422)
