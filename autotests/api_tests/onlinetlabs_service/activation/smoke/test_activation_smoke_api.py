# Smoke tests for the account activation gate.
# An activated user has access to the resources (launching labs, AI);
# require_active_user does not block an active user. Blocking an inactive one (403)
# is covered by the backend unit tests, since the API suite has no source account
# for an inactive user (credential accounts are active).

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import (
    SessionsHelperApi,
)
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_is_not_none


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestActivationSmokeApi:
    """Smoke tests for the activation gate, where an active user is not blocked."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("3491")
    @autotest.external_id("3a985e9f-26b7-4fe1-84dc-9834a296fa67")
    @autotest.name(
        "Smoke: active user passes the activation gate and launches the lab"
    )
    async def test_3a985e9f_active_user_passes_activation_gate(self):
        """An active user does not get a 403 from require_active_user and launches the lab."""
        # Act
        with autotest.step("Active user launches autotest-lab"):
            body = await self.sessions_helper.launch_session("autotest-lab")

        # Assert
        with autotest.step("Activation gate passed: session created (no 403)"):
            assert_is_not_none(
                body.get("session_id"),
                "session_id present — active user not blocked",
            )
