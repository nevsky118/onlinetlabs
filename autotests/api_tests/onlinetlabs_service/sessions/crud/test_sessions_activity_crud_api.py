# CRUD tests for GET activity.

import pytest

from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_in


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestSessionsActivityCrudApi:
    """CRUD tests for /users/me/sessions/{id}/activity."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)

    @autotest.num("77")
    @autotest.external_id("1f6f3836-9fae-4895-b588-c787d2e8910d")
    @autotest.name("Sessions CRUD: activity limit=0 → 422 or 404")
    async def test_1f6f3836_limit_0_422(self):
        """limit=0 gives 422 from FastAPI Query, or 404 for an unknown session, and both are valid."""
        # Act
        with autotest.step("GET activity with limit=0"):
            response = await self.sessions_api.get_session_activity(
                "00000000-0000-0000-0000-000000000000",
                {"limit": 0},
            )

        # Assert
        with autotest.step("Check status code 422 or 404"):
            assert_in(response.status_code, (422, 404), "status code")
