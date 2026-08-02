# CRUD tests for GET /users/me/sessions/{id}/state.

import pytest

from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestSessionsStateCrudApi:
    """CRUD tests for /users/me/sessions/{id}/state."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)

    @autotest.num("74")
    @autotest.external_id("74111111-7777-4777-7777-777777777777")
    @autotest.name("Sessions CRUD: state 404 for an unknown session")
    async def test_74111111_state_404(self):
        """GET state with a nonexistent session_id returns 404."""
        # Act
        with autotest.step("GET state with an all-zero UUID"):
            response = await self.sessions_api.get_session_state(
                "00000000-0000-0000-0000-000000000000",
            )

        # Assert
        with autotest.step("Check status code 404"):
            check_response_status(response, 404)
