# Smoke-тест SSE чат-стрима тьютора POST /chat/stream (Vercel AI SDK v1).

import json

import pytest

from autotests.api.api_methods.onlinetlabs_service.chat_api import ChatApi
from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import SessionsHelperApi
from autotests.settings.constants.constants_settings import ConstantsSettings
from autotests.settings.reports import autotest


def _parse_sse(lines: list[str]) -> tuple[list[dict], bool]:
    """Разбирает SSE-строки в события и флаг [DONE]."""
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
    """Smoke-тест стриминга ответа тьютора через SSE (требует валидного LLM-ключа)."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.chat_api = ChatApi(anon_client, config, ConstantsSettings.REGISTERED_ACCOUNT)
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("59")
    @autotest.external_id("e0f1a2b3-c4d5-6789-efab-890123456789")
    @autotest.name("Smoke: chat/stream — v1 события (start, text-delta, [DONE])")
    async def test_e0f1a2b3_chat_stream_v1_events(self):
        """POST /chat/stream возвращает SSE-поток v1 со start, text-delta и [DONE]."""
        # Arrange
        with autotest.step("Запускаем сессию autotest-lab"):
            launched = await self.sessions_helper.launch_session("autotest-lab")
            session_id = launched["session_id"]

        # Act
        with autotest.step("Отправляем сообщение пользователя в чат-стрим"):
            lines = await self.chat_api.post_chat_stream(
                session_id,
                messages=[{"role": "user", "parts": [{"type": "text", "text": "привет"}]}],
            )

        events, done = _parse_sse(lines)
        types = [e.get("type") for e in events]

        # Assert
        with autotest.step("Проверяем наличие события start"):
            assert "start" in types, f"Ожидали событие start, получили типы: {types}"

        with autotest.step("Проверяем наличие хотя бы одного text-delta"):
            assert "text-delta" in types, f"Ожидали хотя бы один text-delta, получили типы: {types}"

        with autotest.step("Проверяем финальный сигнал [DONE]"):
            assert done, "Ожидали финальный SSE-сигнал [DONE]"

        with autotest.step("Проверяем отсутствие события error"):
            assert "error" not in types, (
                f"Стрим завершился ошибкой: "
                f"{[e for e in events if e.get('type') == 'error']}"
            )
