from datetime import UTC, datetime, timedelta

import pytest
from mcp_sdk.models import LogLevel
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from src.log_buffer import LogBuffer

pytestmark = [pytest.mark.unit, pytest.mark.log_buffer]


class TestLogBuffer:
    @autotest.num("310")
    @autotest.external_id("878cb74b-8699-4eaa-a59d-990705ae41d8")
    @autotest.name("LogBuffer._add_entry: adds an entry")
    def test_878cb74b_add_entry(self):
        with autotest.step("Add an entry"):
            buf = LogBuffer()
            buf._add_entry(LogLevel.INFO, "test message")

        with autotest.step("Assert"):
            logs = buf.get_logs()
            assert_equal(len(logs), 1, "logs count")
            assert_equal(logs[0].message, "test message", "message")
            assert_equal(logs[0].level, LogLevel.INFO, "level")

    @autotest.num("311")
    @autotest.external_id("1c25891a-3078-4ec2-8e6e-a58206a7c2b6")
    @autotest.name("LogBuffer: the ring buffer evicts old entries")
    def test_1c25891a_ring_eviction(self):
        with autotest.step("Fill a buffer with max_entries=3"):
            buf = LogBuffer(max_entries=3)
            for i in range(5):
                buf._add_entry(LogLevel.INFO, f"msg-{i}")

        with autotest.step("Assert only the last 3 remain"):
            logs = buf.get_logs()
            assert_equal(len(logs), 3, "logs count")
            assert_equal(logs[0].message, "msg-2", "message")
            assert_equal(logs[2].message, "msg-4", "message")

    @autotest.num("312")
    @autotest.external_id("c39f3b03-880b-4f77-8882-75ffd1fb7527")
    @autotest.name("LogBuffer.get_errors: only ERROR and WARNING")
    def test_c39f3b03_get_errors(self):
        with autotest.step("Add entries at different levels"):
            buf = LogBuffer()
            buf._add_entry(LogLevel.INFO, "info")
            buf._add_entry(LogLevel.ERROR, "error")
            buf._add_entry(LogLevel.WARNING, "warning")

        with autotest.step("Assert the filtering"):
            errors = buf.get_errors()
            assert_equal(len(errors), 2, "errors count")
            assert_equal(errors[0].message, "error", "message")
            assert_equal(errors[1].message, "warning", "message")

    @autotest.num("313")
    @autotest.external_id("8474a912-0c80-46cf-b52d-d84469072df8")
    @autotest.name("LogBuffer.get_errors: filtering by since")
    def test_8474a912_get_errors_since(self):
        with autotest.step("Add entries"):
            buf = LogBuffer()
            buf._add_entry(LogLevel.ERROR, "old error")
            buf._add_entry(LogLevel.ERROR, "new error")

        with autotest.step("Filter by since (in the future)"):
            future = datetime.now(tz=UTC) + timedelta(seconds=1)
            errors = buf.get_errors(since=future)
            assert_equal(len(errors), 0, "errors count")

    @autotest.num("314")
    @autotest.external_id("4ff0a00c-44f4-4e20-bd80-5b6edf7b2e47")
    @autotest.name("LogBuffer.get_logs: filtering by level")
    def test_4ff0a00c_get_logs_by_level(self):
        with autotest.step("Add entries at different levels"):
            buf = LogBuffer()
            buf._add_entry(LogLevel.INFO, "info-1")
            buf._add_entry(LogLevel.ERROR, "error-1")
            buf._add_entry(LogLevel.INFO, "info-2")

        with autotest.step("Filter by ERROR"):
            logs = buf.get_logs(level=LogLevel.ERROR)
            assert_equal(len(logs), 1, "logs count")
            assert_equal(logs[0].message, "error-1", "message")

        with autotest.step("ALL returns everything"):
            logs = buf.get_logs(level=LogLevel.ALL)
            assert_equal(len(logs), 3, "logs count")

    @autotest.num("315")
    @autotest.external_id("a7636e1b-a5d7-4533-8645-61e16c4d4b1d")
    @autotest.name("LogBuffer.get_logs: limit caps the result")
    def test_a7636e1b_get_logs_limit(self):
        with autotest.step("Add 5 entries"):
            buf = LogBuffer()
            for i in range(5):
                buf._add_entry(LogLevel.INFO, f"msg-{i}")

        with autotest.step("Request limit=2"):
            logs = buf.get_logs(limit=2)
            assert_equal(len(logs), 2, "logs count")
            assert_equal(logs[0].message, "msg-3", "message")
            assert_equal(logs[1].message, "msg-4", "message")

    @autotest.num("316")
    @autotest.external_id("11d7ba5f-24d1-4525-abdc-196d84a28e6f")
    @autotest.name("LogBuffer.close: clears the buffer")
    async def test_11d7ba5f_close(self):
        with autotest.step("Add entries, then close"):
            buf = LogBuffer()
            buf._add_entry(LogLevel.INFO, "msg")
            await buf.close()

        with autotest.step("Buffer is empty"):
            assert_equal(len(buf.get_logs()), 0, "get logs count")
            assert_equal(buf.connected, False, "connected")

    @autotest.num("317")
    @autotest.external_id("63d6372d-f582-4826-8e8b-5b9f85908ce6")
    @autotest.name("LogBuffer: initial state")
    def test_63d6372d_initial_state(self):
        with autotest.step("Create a buffer"):
            buf = LogBuffer(max_entries=100, inactivity_timeout=60.0)

        with autotest.step("Assert"):
            assert_equal(buf.connected, False, "connected")
            assert_equal(len(buf.get_logs()), 0, "get logs count")
            assert_equal(len(buf.get_errors()), 0, "get errors count")
