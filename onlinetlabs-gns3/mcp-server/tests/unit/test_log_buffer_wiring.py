import pytest
from unittest.mock import AsyncMock, patch

from tests.helpers.factories import build_session_context
from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.log_buffer]


class TestLogBufferWiring:
    @autotests.num("390")
    @autotests.external_id("a1b2c3d4-0001-4aaa-bbbb-390000000001")
    @autotests.name("GNS3 Server: _ensure_log_buffer вызывает ensure_connected")
    async def test_ensure_log_buffer_connects(self):
        from src.log_buffer import LogBuffer
        from src.server import GNS3Server

        log_buffer = LogBuffer()
        server = GNS3Server(api_client=None, log_buffer=log_buffer)
        ctx = build_session_context()

        with autotests.step("Мокаем ensure_connected"):
            log_buffer.ensure_connected = AsyncMock()

        with autotests.step("Вызываем _ensure_log_buffer"):
            await server._ensure_log_buffer(ctx)

        with autotests.step("Проверяем вызов ensure_connected"):
            log_buffer.ensure_connected.assert_called_once()
            call_args = log_buffer.ensure_connected.call_args
            ws_url = call_args[0][0]
            assert "notifications/ws" in ws_url
            assert ws_url.startswith("ws://")

    @autotests.num("391")
    @autotests.external_id("a1b2c3d4-0002-4aaa-bbbb-391000000001")
    @autotests.name("GNS3 Server: _ensure_log_buffer создаёт буфер если None")
    async def test_ensure_log_buffer_creates_if_none(self):
        from src.server import GNS3Server

        server = GNS3Server(api_client=None, log_buffer=None)
        ctx = build_session_context()

        with autotests.step("Мокаем LogBuffer"):
            with patch("src.server.LogBuffer") as MockBuffer:
                mock_instance = MockBuffer.return_value
                mock_instance.ensure_connected = AsyncMock()
                await server._ensure_log_buffer(ctx)

        with autotests.step("Проверяем что буфер создан"):
            assert server._log_buffer is not None
