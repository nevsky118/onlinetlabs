# E2E (Tier 2): после чата в БД появляются chat_messages (+usage).

import pytest

pytest.importorskip("pydantic_ai")  # Tier 2: бежит только в backend-venv, иначе module-level skip

from autotests.api.api_helpers.e2e.db_readback_helper import fetch_chat_messages
from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.api.api_methods.onlinetlabs_service.chat_api import ChatApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_greater_equal, assert_in


@pytest.mark.e2e
@pytest.mark.asyncio
class TestDataRecordingE2E:
    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        acc = ConstantsSettings.REGISTERED_ACCOUNT
        self.chat_api = ChatApi(anon_client, config, acc)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("710")
    @autotest.external_id("d1e2f3a4-b5c6-7890-defa-710000000001")
    @autotest.name("E2E: чат пишет chat_messages (user+assistant) в БД")
    async def test_d1e2f3a4_chat_persisted(self):
        with autotest.step("Launch + чат"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]
            await self.chat_api.post_chat_stream(
                session_id,
                messages=[{"role": "user", "parts": [{"type": "text", "text": "Что такое trunk?"}]}],
            )

        with autotest.step("Read-back БД — есть user и assistant сообщения"):
            rows = await fetch_chat_messages(session_id)
            roles = [r.role for r in rows]
            assert_greater_equal(len(rows), 2, "минимум 2 сообщения")
            assert_in("user", roles, "есть user")
            assert_in("assistant", roles, "есть assistant")
