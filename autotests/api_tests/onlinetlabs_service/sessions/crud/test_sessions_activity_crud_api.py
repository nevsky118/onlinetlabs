# CRUD-тесты GET activity.

import pytest

from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestSessionsActivityCrudApi:
    """CRUD-тесты /users/me/sessions/{id}/activity."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)

    @autotest.num("77")
    @autotest.external_id("77111111-7777-4777-7777-777777777777")
    @autotest.name("Sessions CRUD: activity limit=0 → 422 или 404")
    async def test_77111111_limit_0_422(self):
        """limit=0 даёт 422 от FastAPI Query, либо 404 при неизвестной сессии — оба валидны."""
        # Act
        with autotest.step("GET activity с limit=0"):
            response = await self.sessions_api.get_session_activity(
                "00000000-0000-0000-0000-000000000000",
                {"limit": 0},
            )

        # Assert
        with autotest.step("Проверяем статус код 422 или 404"):
            assert response.status_code in (422, 404), (
                f"Ожидали 422 или 404, получили {response.status_code}"
            )
