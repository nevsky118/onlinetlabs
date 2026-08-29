# E2E: end-to-end student path (HTTP), browsing → launch → chat → progress → lifecycle → end.


import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.chat_api import ChatApi
from autotests.api.api_methods.onlinetlabs_service.courses_api import CoursesApi
from autotests.api.api_methods.onlinetlabs_service.labs_api import LabsApi
from autotests.api.api_methods.onlinetlabs_service.progress_api import ProgressApi
from autotests.api.api_methods.onlinetlabs_service.sessions_api import SessionsApi
from autotests.api.data.onlinetlabs_service.progress_data_api import StepAttemptData
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import (
    assert_equal,
    assert_in,
    assert_is_not_none,
    assert_true,
)
from autotests.settings.utils.utils import check_response_status
from autotests.api.api_helpers.onlinetlabs_service.sse_helper_api import SseHelper

_LAB = "autotest-lab"
_STEP = "step-1"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestStudentJourneyE2E:
    """E2E end-to-end student path over HTTP."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        acc = ConstantsSettings.REGISTERED_ACCOUNT
        self.courses_api = CoursesApi(anon_client, config)
        self.labs_api = LabsApi(anon_client, config, acc)
        self.progress_api = ProgressApi(anon_client, config, acc)
        self.chat_api = ChatApi(anon_client, config, acc)
        self.sessions_api = SessionsApi(anon_client, config, acc)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("3487")
    @autotest.external_id("de5178f0-ac90-49f6-930e-edbe1f8f6dbd")
    @autotest.name("E2E: student journey — browsing→launch→chat→progress→lifecycle→end")
    async def test_de5178f0_student_journey(self):
        with autotest.step("Browsing courses and labs"):
            check_response_status(await self.courses_api.get_courses(), 200)
            check_response_status(await self.labs_api.get_labs(), 200)
            check_response_status(await self.labs_api.get_lab_by_slug(_LAB), 200)

        with autotest.step("Start progress on lab"):
            post_start_lab = await self.progress_api.post_start_lab(_LAB)
            assert_true(post_start_lab.status_code in (200, 201), f"start_lab status {post_start_lab.status_code}")

        with autotest.step("Launch session"):
            launched = await self.sessions_helper.launch_session(_LAB)
            session_id = launched["session_id"]
            assert_is_not_none(session_id, "session_id present")
            assert_true("gns3-server" not in launched["gns3_url"], "gns3_url is public")

        with autotest.step("GET session — active + lab_title"):
            resp = await self.sessions_api.get_session(session_id)
            check_response_status(resp, 200)
            body = resp.json()
            assert_equal(body["status"], "active", "status active")
            assert_equal(body["lab_title"], "Autotest Lab", "lab_title")

        with autotest.step("Chat — SSE streams tokens"):
            lines = await self.chat_api.post_chat_stream(
                session_id,
                messages=[{"role": "user", "parts": [{"type": "text", "text": "Что такое VLAN?"}]}],
            )
            types, done = SseHelper.parse_event_types(lines)
            assert_in("start", types, "event start")
            assert_in("text-delta", types, "event text-delta")
            assert_true(done, "stream finished [DONE]")
            assert_true("error" not in types, "no error")

        with autotest.step("Record step attempts — fail then pass"):
            r1 = await self.progress_api.post_step_attempt(
                _LAB, _STEP, StepAttemptData(result="fail", score=0.0, error_details={"msg": "bad vlan"}).data)
            check_response_status(r1, 200)
            r2 = await self.progress_api.post_step_attempt(
                _LAB, _STEP, StepAttemptData(result="pass", score=1.0, error_details=None).data)
            check_response_status(r2, 200)
            assert_true(r2.json()["attempt_number"] > r1.json()["attempt_number"], "attempt number increases")

        with autotest.step("Readback progress — attempts recorded"):
            detail = await self.progress_api.get_lab_progress(_LAB)
            check_response_status(detail, 200)
            results = [
            attempt["result"]
            for attempt in detail.json()["attempts"]
            if attempt["step_slug"] == _STEP
        ]
            assert_in("fail", results, "fail present")
            assert_in("pass", results, "pass present")

        with autotest.step("Lifecycle: stop/restart/reset"):
            check_response_status(await self.sessions_api.post_stop(session_id), 200)
            check_response_status(await self.sessions_api.post_restart(session_id), 200)
            check_response_status(await self.sessions_api.post_reset(session_id), 200)

        with autotest.step("End — status ended"):
            check_response_status(await self.sessions_api.post_end(session_id), 200)
            ended = await self.sessions_api.get_session(session_id)
            assert_equal(ended.json()["status"], "ended", "status ended")
