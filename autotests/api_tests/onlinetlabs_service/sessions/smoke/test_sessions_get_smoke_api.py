# Smoke-тест получения сессии по id GET /users/me/sessions/{session_id}.

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestSessionsGetSmokeApi:
    """Smoke-тест GET /users/me/sessions/{session_id}."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("60")
    @autotest.external_id("a2b3c4d5-e6f7-8901-abcd-ef0123456790")
    @autotest.name("Smoke: GET /users/me/sessions/{id} — 200, тело содержит lab_slug и status")
    async def test_a2b3c4d5_get_session_by_id(self):
        """GET по id возвращает 200 с lab_slug и status запущенной сессии."""
        with autotest.step("Запускаем сессию autotest-lab"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        with autotest.step("Запрашиваем сессию по id"):
            response = await self.sessions_api.get_session(session_id)

        check_response_status(response, 200)
        body = response.json()

        with autotest.step("Проверяем lab_slug"):
            assert body.get("lab_slug") == "autotest-lab", f"Ожидали lab_slug=autotest-lab, получили: {body.get('lab_slug')}"

        with autotest.step("Проверяем status=active"):
            assert body.get("status") == "active", f"Ожидали status=active, получили: {body.get('status')}"

        with autotest.step("Проверяем lab_title"):
            assert body.get("lab_title") == "Autotest Lab", f"Ожидали lab_title=Autotest Lab, получили: {body.get('lab_title')}"
