# CRUD tests for POST /auth/login.

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
    """CRUD tests for POST /auth/login."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.auth_helper = AuthHelperApi(anon_client, config)
        self.auth_api = AuthApi(anon_client, config)

    @autotest.num("5")
    @autotest.external_id("a1341411-f699-49f9-bf70-1cfad241f2a1")
    @autotest.name("Auth Login: success (200)")
    async def test_a1341411_login_success(self):
        """A successful login after registration returns 200."""
        # Arrange
        with autotest.step("Register user"):
            reg_data = AuthRegisterData()
            await self.auth_helper.register_user(reg_data.data)

        with autotest.step("Build login payload from the registered user"):
            login_data = {
                "email": reg_data.email,
                "password": reg_data.password,
            }

        # Act
        with autotest.step("Log in with correct credentials"):
            response = await self.auth_api.post_login(data=login_data)

        # Assert
        with autotest.step("Verify status code 200"):
            check_response_status(response, 200)

    @autotest.num("6")
    @autotest.external_id("2a515cc0-a06e-4f9a-97e6-713bb8c25763")
    @autotest.name("Auth Login: wrong password (401)")
    async def test_2a515cc0_login_wrong_password(self):
        """A login with a wrong password returns 401."""
        # Arrange
        with autotest.step("Register user"):
            reg_data = AuthRegisterData()
            await self.auth_helper.register_user(reg_data.data)

        with autotest.step("Build login payload with a wrong password"):
            login_data = {
                "email": reg_data.email,
                "password": valid_password(),
            }

        # Act
        with autotest.step("Log in with wrong password"):
            response = await self.auth_api.post_login(data=login_data)

        # Assert
        with autotest.step("Verify status code 401"):
            check_response_status(response, 401)

    @autotest.num("7")
    @autotest.external_id("7467ff96-7727-485c-a44f-3683b4d18665")
    @autotest.name("Auth Login: non-existent email (401)")
    async def test_7467ff96_login_nonexistent_email(self):
        """A login with a nonexistent email returns 401."""
        # Arrange
        with autotest.step("Build login payload for a nonexistent email"):
            login_data = AuthLoginData()

        # Act
        with autotest.step("Log in with nonexistent email"):
            response = await self.auth_api.post_login(data=login_data.data)

        # Assert
        with autotest.step("Verify status code 401"):
            check_response_status(response, 401)
