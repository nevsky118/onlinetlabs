"""Test: log buffers are keyed per (user, project), not shared process-wide."""

from unittest.mock import AsyncMock

import pytest
from mcp_sdk.context import SessionContext
from mcp_sdk.testing import autotest

from src.server import GNS3Server

pytestmark = [pytest.mark.unit]

GNS3_URL = "http://gns3:3080"


def _ctx(user_id: str, project_id: str) -> SessionContext:
    return SessionContext(
        user_id=user_id,
        session_id=f"s-{user_id}",
        environment_url=GNS3_URL,
        project_id=project_id,
    )


def _buffer_factory():
    buffer = AsyncMock()
    buffer.get_errors.return_value = []
    buffer.get_logs.return_value = []
    return buffer


class TestLogBufferIsolation:
    @autotest.num("860")
    @autotest.external_id("a8cef971-718d-4efa-a7c9-2bef5490bae2")
    @autotest.name("LogBuffer: different users get different buffers")
    async def test_a8cef971_separate_buffers_per_user(self):
        with autotest.step("Arrange: server with a buffer factory"):
            server = GNS3Server(api_client=AsyncMock(), log_buffer_factory=_buffer_factory)

        with autotest.step("Act: two students on two projects read logs"):
            first = await server._ensure_log_buffer(_ctx("u1", "p1"))
            second = await server._ensure_log_buffer(_ctx("u2", "p2"))

        with autotest.step("Assert: two buffers, each connected to its own project"):
            assert first is not second
            assert len(server._log_buffers) == 2
            assert "p1" in first.ensure_connected.await_args.args[0]
            assert "p2" in second.ensure_connected.await_args.args[0]

    @autotest.num("861")
    @autotest.external_id("e0363a2c-0fe6-4d78-a5df-45ddef3dbfc8")
    @autotest.name("LogBuffer: the same session reuses its buffer")
    async def test_e0363a2c_same_session_reuses_buffer(self):
        with autotest.step("Arrange: server with a buffer factory"):
            server = GNS3Server(api_client=AsyncMock(), log_buffer_factory=_buffer_factory)

        with autotest.step("Act: the same student reads twice"):
            first = await server._ensure_log_buffer(_ctx("u1", "p1"))
            second = await server._ensure_log_buffer(_ctx("u1", "p1"))

        with autotest.step("Assert: one buffer is kept"):
            assert first is second
            assert len(server._log_buffers) == 1
