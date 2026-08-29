# Smoke test for the tutor SSE chat stream POST /chat/stream (Vercel AI SDK v1).


import pytest

from autotests.api.api_methods.onlinetlabs_service.chat_api import ChatApi
from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_false, assert_in, assert_true
from autotests.api.api_helpers.onlinetlabs_service.sse_helper_api import SseHelper


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestChatStreamSmokeApi:
    """Smoke test for streaming the tutor response over SSE (requires a valid LLM key)."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.chat_api = ChatApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("59")
    @autotest.external_id("9a6d1d09-16ff-4261-b6a1-4e86fa3386ca")
    @autotest.name("Smoke: chat/stream — v1 events (start, text-delta, [DONE])")
    async def test_9a6d1d09_chat_stream_v1_events(self):
        """POST /chat/stream returns a v1 SSE stream with start, text-delta and [DONE]."""
        # Arrange
        with autotest.step("Launch autotest-lab session"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        # Act
        with autotest.step("Send user message to chat stream"):
            lines = await self.chat_api.post_chat_stream(
                session_id,
                messages=[{"role": "user", "parts": [{"type": "text", "text": "привет"}]}],
            )

        with autotest.step("Act: parse the SSE stream into events and types"):
            events, done = SseHelper.parse_events(lines)
            types = [event.get("type") for event in events]

        # Assert
        with autotest.step("Verify start event present"):
            assert_in("start", types, "'start'")

        with autotest.step("Verify at least one text-delta present"):
            assert_in("text-delta", types, "'text-delta'")

        with autotest.step("Verify final [DONE] signal"):
            assert_true(done, "Expected final SSE signal [DONE]")

        with autotest.step("Verify no error event"):
            assert_false("error" in types, "'error' absent")
