# Smoke test for the tutor SSE chat stream POST /chat/stream (Vercel AI SDK v1).

import json

import pytest

from autotests.api.api_methods.onlinetlabs_service.chat_api import ChatApi
from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


def _parse_sse(lines: list[str]) -> tuple[list[dict], bool]:
    """Parses SSE lines into events and the [DONE] flag."""
    events: list[dict] = []
    done = False
    for line in lines:
        if not line.startswith("data: "):
            continue
        payload = line[len("data: "):]
        if payload == "[DONE]":
            done = True
            continue
        events.append(json.loads(payload))
    return events, done


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
    @autotest.external_id("e0f1a2b3-c4d5-6789-efab-890123456789")
    @autotest.name("Smoke: chat/stream — v1 events (start, text-delta, [DONE])")
    async def test_e0f1a2b3_chat_stream_v1_events(self):
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

        events, done = _parse_sse(lines)
        types = [e.get("type") for e in events]

        # Assert
        with autotest.step("Verify start event present"):
            assert "start" in types, f"Expected start event, got types: {types}"

        with autotest.step("Verify at least one text-delta present"):
            assert "text-delta" in types, f"Expected at least one text-delta, got types: {types}"

        with autotest.step("Verify final [DONE] signal"):
            assert done, "Expected final SSE signal [DONE]"

        with autotest.step("Verify no error event"):
            assert "error" not in types, (
                f"Stream ended with error: "
                f"{[e for e in events if e.get('type') == 'error']}"
            )
