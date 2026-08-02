# CRUD tests for the session lifecycle of /users/me/sessions.

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_is_not_none
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
    @autotest.external_id("c2d3e4f5-a6b7-8901-cdef-012345678901")
    @autotest.name("CRUD: relaunch autotest-lab — idempotency (same session_id)")
    async def test_c2d3e4f5_relaunch_idempotent(self):
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
            assert body.get("session_id") == session_id, (
                f"Expected session_id={session_id}, got: {body.get('session_id')}"
            )

    @autotest.num("52")
    @autotest.external_id("d3e4f5a6-b7c8-9012-defa-123456789012")
    @autotest.name("CRUD: GET credentials — 200, returns gns3_username/password/url")
    async def test_d3e4f5a6_get_credentials(self):
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
    @autotest.external_id("e4f5a6b7-c8d9-0123-efab-234567890123")
    @autotest.name("CRUD: POST stop — 200 {ok: true}")
    async def test_e4f5a6b7_stop(self):
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
            assert response.json() == {"ok": True}, f"Expected {{ok: true}}, got: {response.json()}"

    @autotest.num("54")
    @autotest.external_id("f5a6b7c8-d9e0-1234-fabc-345678901234")
    @autotest.name("CRUD: POST restart — 200 {ok: true}")
    async def test_f5a6b7c8_restart(self):
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
            assert response.json() == {"ok": True}, f"Expected {{ok: true}}, got: {response.json()}"

    @autotest.num("55")
    @autotest.external_id("a6b7c8d9-e0f1-2345-abcd-456789012345")
    @autotest.name("CRUD: POST reset — 200 {ok: true}")
    async def test_a6b7c8d9_reset(self):
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
            assert response.json() == {"ok": True}, f"Expected {{ok: true}}, got: {response.json()}"

    @autotest.num("56")
    @autotest.external_id("b7c8d9e0-f1a2-3456-bcde-567890123456")
    @autotest.name("CRUD: POST end — 200 {ok: true}, relaunch creates a new session")
    async def test_b7c8d9e0_end_and_relaunch(self):
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
            assert end_response.json() == {"ok": True}, f"Expected {{ok: true}}, got: {end_response.json()}"

        # Act — relaunch after end
        with autotest.step("Relaunch the session after end"):
            relaunch = await self.sessions_helper.launch_session("autotest-lab")
            new_session_id = relaunch["session_id"]

        # Assert — new session created
        with autotest.step("Check that the new session has a different session_id"):
            assert new_session_id != session_id, (
                f"Expected a new session_id, but got the same one: {new_session_id}"
            )

    @autotest.num("57")
    @autotest.external_id("c8d9e0f1-a2b3-4567-cdef-678901234567")
    @autotest.name("CRUD: ownership — another user's token on credentials → 404")
    async def test_c8d9e0f1_ownership_credentials(self):
        """Another user's token when accessing credentials results in 404."""
        # Arrange
        with autotest.step("Register a session from REGISTERED_ACCOUNT"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        # Act — request with ANON_ACCOUNT token
        with autotest.step(f"GET credentials with the ANON_ACCOUNT token → expect 404"):
            response = await self.sessions_api_anon.get_credentials(session_id)

        # Assert
        with autotest.step("Check status code 404"):
            check_response_status(response, 404)

    @autotest.num("58")
    @autotest.external_id("d9e0f1a2-b3c4-5678-defa-789012345678")
    @autotest.name("CRUD: ownership — another user's token on stop → 404")
    async def test_d9e0f1a2_ownership_stop(self):
        """Another user's token on POST stop results in 404."""
        # Arrange
        with autotest.step("Register a session from REGISTERED_ACCOUNT"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        # Act
        with autotest.step(f"POST stop with the ANON_ACCOUNT token → expect 404"):
            response = await self.sessions_api_anon.post_stop(session_id)

        # Assert
        with autotest.step("Check status code 404"):
            check_response_status(response, 404)
