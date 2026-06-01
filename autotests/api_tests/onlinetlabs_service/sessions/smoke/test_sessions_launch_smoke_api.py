# Smoke-тесты запуска сессии /users/me/sessions (launch lifecycle).

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_is_not_none
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestSessionsLaunchSmokeApi:
    """Smoke-тесты запуска лабораторной сессии /users/me/sessions."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("50")
    @autotest.external_id("b1c2d3e4-f5a6-7890-bcde-f01234567890")
    @autotest.name("Smoke: POST /users/me/sessions — 201 launch autotest-lab, тело содержит session_id/gns3_*/status=active")
    async def test_b1c2d3e4_launch_autotest_lab(self):
        """Запуск autotest-lab возвращает 201 с полным телом ответа и status=active."""
        # Act
        with autotest.step("Запускаем сессию для autotest-lab через хелпер"):
            body = await self.sessions_helper.launch_session("autotest-lab")

        # Assert
        with autotest.step("Проверяем наличие session_id"):
            assert_is_not_none(body.get("session_id"), "session_id не должен быть None")

        with autotest.step("Проверяем status=active"):
            assert body.get("status") == "active", f"Ожидали status=active, получили: {body.get('status')}"

        with autotest.step("Проверяем наличие gns3_username"):
            assert_is_not_none(body.get("gns3_username"), "gns3_username не должен быть None")

        with autotest.step("Проверяем наличие gns3_password"):
            assert_is_not_none(body.get("gns3_password"), "gns3_password не должен быть None")

        with autotest.step("Проверяем наличие gns3_url"):
            assert_is_not_none(body.get("gns3_url"), "gns3_url не должен быть None")

        with autotest.step("Проверяем gns3_url использует публичный хост, не Docker-internal"):
            assert "gns3-server" not in body["gns3_url"], (
                f"gns3_url должен быть browser-reachable (public), получили: {body['gns3_url']}"
            )
