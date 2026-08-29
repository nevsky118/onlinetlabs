# CRUD tests for the session lifecycle of /users/me/sessions.

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_equal, assert_is_not_none, assert_not_equal
from autotests.settings.utils.utils import check_response_status


@pytest.mark.api
@pytest.mark.crud
@pytest.mark.asyncio
class TestSessionsLifecycleCrudApi:
    """CRUD tests for the lab session lifecycle."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_api = SessionsApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_api_anon = SessionsApi(anon_client, config, ConstantsSettings.ANON_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("51")
    @autotest.external_id("81b0f0a4-13a0-4912-90ad-5cb8919f1ffc")
    @autotest.name("CRUD: relaunch autotest-lab — idempotency (same session_id)")
    async def test_81b0f0a4_relaunch_idempotent(self):
        """Relaunching an active session returns the same session_id."""
        # Arrange
        with autotest.step("Launch the session for the first time"):
            first = await self.sessions_helper.launch_session("autotest-lab")
            session_id = first["session_id"]

        # Act
        with autotest.step("Launch the session again (should be idempotent)"):
            response = await self.sessions_api.post_session({"lab_slug": "autotest-lab"})

        # Assert
        with autotest.step("Check status code 201"):
            check_response_status(response, 201)

        with autotest.step("Check that session_id did not change"):
            body = response.json()
            assert_equal(body.get("session_id"), session_id, "get")

    @autotest.num("52")
    @autotest.external_id("cc04a575-ddbe-4aa3-822c-5847bd1d5bcf")
    @autotest.name("CRUD: GET credentials — 200, returns gns3_username/password/url")
    async def test_cc04a575_get_credentials(self):
        """GET credentials of an active session returns 200 with the gns3 fields."""
        # Arrange
        with autotest.step("Launch the session"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        # Act
        with autotest.step(f"GET /users/me/sessions/{session_id}/credentials"):
            response = await self.sessions_api.get_credentials(session_id)

        # Assert
        with autotest.step("Check status code 200"):
            check_response_status(response, 200)

        with autotest.step("Check response body contains gns3_username"):
            body = response.json()
            assert_is_not_none(body.get("gns3_username"), "gns3_username must not be None")

        with autotest.step("Check response body contains gns3_password"):
            assert_is_not_none(body.get("gns3_password"), "gns3_password must not be None")

        with autotest.step("Check response body contains gns3_url"):
            assert_is_not_none(body.get("gns3_url"), "gns3_url must not be None")

    @autotest.num("53")
    @autotest.external_id("13d446ad-4bf0-4c76-8d9b-34d4c317e9f0")
    @autotest.name("CRUD: POST stop — 200 {ok: true}")
    async def test_13d446ad_stop(self):
        """POST stop returns 200 with the body {ok: true}."""
        # Arrange
        with autotest.step("Launch the session"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        # Act
        with autotest.step(f"POST /users/me/sessions/{session_id}/stop"):
            response = await self.sessions_api.post_stop(session_id)

        # Assert
        with autotest.step("Check status code 200"):
            check_response_status(response, 200)

        with autotest.step("Check body {ok: true}"):
            assert_equal(response.json(), {"ok": True}, "json")

    @autotest.num("54")
    @autotest.external_id("aa41e3a9-7705-4c3c-a687-8eec71420767")
    @autotest.name("CRUD: POST restart — 200 {ok: true}")
    async def test_aa41e3a9_restart(self):
        """POST restart returns 200 with the body {ok: true}."""
        # Arrange
        with autotest.step("Launch the session"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        # Act
        with autotest.step(f"POST /users/me/sessions/{session_id}/restart"):
            response = await self.sessions_api.post_restart(session_id)

        # Assert
        with autotest.step("Check status code 200"):
            check_response_status(response, 200)

        with autotest.step("Check body {ok: true}"):
            assert_equal(response.json(), {"ok": True}, "json")

    @autotest.num("55")
    @autotest.external_id("c0aaca3c-e670-4aba-8769-18d0c1cf2979")
    @autotest.name("CRUD: POST reset — 200 {ok: true}")
    async def test_c0aaca3c_reset(self):
        """POST reset returns 200 with the body {ok: true}."""
        # Arrange
        with autotest.step("Launch the session"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        # Act
        with autotest.step(f"POST /users/me/sessions/{session_id}/reset"):
            response = await self.sessions_api.post_reset(session_id)

        # Assert
        with autotest.step("Check status code 200"):
            check_response_status(response, 200)

        with autotest.step("Check body {ok: true}"):
            assert_equal(response.json(), {"ok": True}, "json")

    @autotest.num("56")
    @autotest.external_id("57ae6f91-abc0-42e9-8847-6ed3685c9f5e")
    @autotest.name("CRUD: POST end — 200 {ok: true}, relaunch creates a new session")
    async def test_57ae6f91_end_and_relaunch(self):
        """POST end finishes the session, and a relaunch creates a new session_id."""
        # Arrange
        with autotest.step("Launch the first session"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        # Act — end
        with autotest.step(f"POST /users/me/sessions/{session_id}/end"):
            end_response = await self.sessions_api.post_end(session_id)

        # Assert end
        with autotest.step("Check status code 200 for end"):
            check_response_status(end_response, 200)

        with autotest.step("Check body {ok: true}"):
            assert_equal(end_response.json(), {"ok": True}, "json")

        # Act — relaunch after end
        with autotest.step("Relaunch the session after end"):
            relaunch = await self.sessions_helper.launch_session("autotest-lab")
            new_session_id = relaunch["session_id"]

        # Assert — new session created
        with autotest.step("Check that the new session has a different session_id"):
            assert_not_equal(new_session_id, session_id, "new session id")

    @autotest.num("57")
    @autotest.external_id("280a74b1-653c-4b27-abee-3e3ce988f76c")
    @autotest.name("CRUD: ownership — another user's token on credentials → 404")
    async def test_280a74b1_ownership_credentials(self):
        """Another user's token when accessing credentials results in 404."""
        # Arrange
        with autotest.step("Register a session from REGISTERED_ACCOUNT"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        # Act — request with ANON_ACCOUNT token
        with autotest.step("GET credentials with the ANON_ACCOUNT token → expect 404"):
            response = await self.sessions_api_anon.get_credentials(session_id)

        # Assert
        with autotest.step("Check status code 404"):
            check_response_status(response, 404)

    @autotest.num("58")
    @autotest.external_id("8de1fc0e-1002-4ae5-be30-e1774a6bfc03")
    @autotest.name("CRUD: ownership — another user's token on stop → 404")
    async def test_8de1fc0e_ownership_stop(self):
        """Another user's token on POST stop results in 404."""
        # Arrange
        with autotest.step("Register a session from REGISTERED_ACCOUNT"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        # Act
        with autotest.step("POST stop with the ANON_ACCOUNT token → expect 404"):
            response = await self.sessions_api_anon.post_stop(session_id)

        # Assert
        with autotest.step("Check status code 404"):
            check_response_status(response, 404)
