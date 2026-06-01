# E2E: сквозной путь студента (HTTP) — браузинг → launch → чат → прогресс → lifecycle → end.

import json

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

_LAB = "autotest-lab"
_STEP = "step-1"


def _parse_sse(lines: list[str]) -> tuple[set[str], bool]:
    types: set[str] = set()
    done = False
    for line in lines:
        if not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        if payload == "[DONE]":
            done = True
            continue
        try:
            evt = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(evt, dict) and "type" in evt:
            types.add(evt["type"])
    return types, done


@pytest.mark.e2e
@pytest.mark.asyncio
class TestStudentJourneyE2E:
    """E2E сквозной путь студента по HTTP."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        acc = ConstantsSettings.REGISTERED_ACCOUNT
        self.courses_api = CoursesApi(anon_client, config)
        self.labs_api = LabsApi(anon_client, config, acc)
        self.progress_api = ProgressApi(anon_client, config, acc)
        self.chat_api = ChatApi(anon_client, config, acc)
        self.sessions_api = SessionsApi(anon_client, config, acc)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("800")
    @autotest.external_id("c1d2e3f4-a5b6-7890-cdef-800000000001")
    @autotest.name("E2E: путь студента — браузинг→launch→чат→прогресс→lifecycle→end")
    async def test_c1d2e3f4_student_journey(self):
        with autotest.step("Браузинг курсов и лаб"):
            check_response_status(await self.courses_api.get_courses(), 200)
            check_response_status(await self.labs_api.get_labs(), 200)
            check_response_status(await self.labs_api.get_lab_by_slug(_LAB), 200)

        with autotest.step("Старт прогресса по лабе"):
            r = await self.progress_api.post_start_lab(_LAB)
            assert_true(r.status_code in (200, 201), f"start_lab статус {r.status_code}")

        with autotest.step("Launch сессии"):
            launched = await self.sessions_helper.launch_session(_LAB)
            session_id = launched["session_id"]
            assert_is_not_none(session_id, "session_id есть")
            assert_true("gns3-server" not in launched["gns3_url"], "gns3_url публичный")

        with autotest.step("GET сессии — active + lab_title"):
            resp = await self.sessions_api.get_session(session_id)
            check_response_status(resp, 200)
            body = resp.json()
            assert_equal(body["status"], "active", "статус active")
            assert_equal(body["lab_title"], "Autotest Lab", "lab_title")

        with autotest.step("Чат — SSE стримит токены"):
            lines = await self.chat_api.post_chat_stream(
                session_id,
                messages=[{"role": "user", "parts": [{"type": "text", "text": "Что такое VLAN?"}]}],
            )
            types, done = _parse_sse(lines)
            assert_in("start", types, "событие start")
            assert_in("text-delta", types, "событие text-delta")
            assert_true(done, "поток завершён [DONE]")
            assert_true("error" not in types, "нет error")

        with autotest.step("Запись попыток шага — fail затем pass"):
            r1 = await self.progress_api.post_step_attempt(
                _LAB, _STEP, StepAttemptData(result="fail", score=0.0, error_details={"msg": "bad vlan"}).data)
            check_response_status(r1, 200)
            r2 = await self.progress_api.post_step_attempt(
                _LAB, _STEP, StepAttemptData(result="pass", score=1.0, error_details=None).data)
            check_response_status(r2, 200)
            assert_true(r2.json()["attempt_number"] > r1.json()["attempt_number"], "номер попытки растёт")

        with autotest.step("Readback прогресса — попытки записаны"):
            detail = await self.progress_api.get_lab_progress(_LAB)
            check_response_status(detail, 200)
            results = [a["result"] for a in detail.json()["attempts"] if a["step_slug"] == _STEP]
            assert_in("fail", results, "есть fail")
            assert_in("pass", results, "есть pass")

        with autotest.step("Lifecycle: stop/restart/reset"):
            check_response_status(await self.sessions_api.post_stop(session_id), 200)
            check_response_status(await self.sessions_api.post_restart(session_id), 200)
            check_response_status(await self.sessions_api.post_reset(session_id), 200)

        with autotest.step("End — статус ended"):
            check_response_status(await self.sessions_api.post_end(session_id), 200)
            ended = await self.sessions_api.get_session(session_id)
            assert_equal(ended.json()["status"], "ended", "статус ended")
