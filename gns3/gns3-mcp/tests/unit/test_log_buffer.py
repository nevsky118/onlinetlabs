from datetime import UTC, datetime, timedelta

import pytest
from mcp_sdk.models import LogLevel
from mcp_sdk.testing import autotest

from src.log_buffer import LogBuffer

pytestmark = [pytest.mark.unit, pytest.mark.log_buffer]


class TestLogBuffer:
    @autotest.num("310")
    @autotest.external_id("gns3-log-buffer-add-entry")
    @autotest.name("LogBuffer._add_entry: adds an entry")
    def test_add_entry(self):
        with autotest.step("Add an entry"):
            buf = LogBuffer()
            buf._add_entry(LogLevel.INFO, "test message")

        with autotest.step("Assert"):
            logs = buf.get_logs()
            assert len(logs) == 1
            assert logs[0].message == "test message"
            assert logs[0].level == LogLevel.INFO

    @autotest.num("311")
    @autotest.external_id("gns3-log-buffer-ring-eviction")
    @autotest.name("LogBuffer: the ring buffer evicts old entries")
    def test_ring_eviction(self):
        with autotest.step("Fill a buffer with max_entries=3"):
            buf = LogBuffer(max_entries=3)
            for i in range(5):
                buf._add_entry(LogLevel.INFO, f"msg-{i}")

        with autotest.step("Assert only the last 3 remain"):
            logs = buf.get_logs()
            assert len(logs) == 3
            assert logs[0].message == "msg-2"
            assert logs[2].message == "msg-4"

    @autotest.num("312")
    @autotest.external_id("gns3-log-buffer-get-errors")
    @autotest.name("LogBuffer.get_errors: only ERROR and WARNING")
    def test_get_errors(self):
        with autotest.step("Add entries at different levels"):
            buf = LogBuffer()
            buf._add_entry(LogLevel.INFO, "info")
            buf._add_entry(LogLevel.ERROR, "error")
            buf._add_entry(LogLevel.WARNING, "warning")

        with autotest.step("Assert the filtering"):
            errors = buf.get_errors()
            assert len(errors) == 2
            assert errors[0].message == "error"
            assert errors[1].message == "warning"

    @autotest.num("313")
    @autotest.external_id("gns3-log-buffer-get-errors-since")
    @autotest.name("LogBuffer.get_errors: filtering by since")
    def test_get_errors_since(self):
        with autotest.step("Add entries"):
            buf = LogBuffer()
            buf._add_entry(LogLevel.ERROR, "old error")
            buf._add_entry(LogLevel.ERROR, "new error")

        with autotest.step("Filter by since (in the future)"):
            future = datetime.now(tz=UTC) + timedelta(seconds=1)
            errors = buf.get_errors(since=future)
            assert len(errors) == 0

    @autotest.num("314")
    @autotest.external_id("gns3-log-buffer-get-logs-by-level")
    @autotest.name("LogBuffer.get_logs: filtering by level")
    def test_get_logs_by_level(self):
        with autotest.step("Add entries at different levels"):
            buf = LogBuffer()
            buf._add_entry(LogLevel.INFO, "info-1")
            buf._add_entry(LogLevel.ERROR, "error-1")
            buf._add_entry(LogLevel.INFO, "info-2")

        with autotest.step("Filter by ERROR"):
            logs = buf.get_logs(level=LogLevel.ERROR)
            assert len(logs) == 1
            assert logs[0].message == "error-1"

        with autotest.step("ALL returns everything"):
            logs = buf.get_logs(level=LogLevel.ALL)
            assert len(logs) == 3

    @autotest.num("315")
    @autotest.external_id("gns3-log-buffer-get-logs-limit")
    @autotest.name("LogBuffer.get_logs: limit caps the result")
    def test_get_logs_limit(self):
        with autotest.step("Add 5 entries"):
            buf = LogBuffer()
            for i in range(5):
                buf._add_entry(LogLevel.INFO, f"msg-{i}")

        with autotest.step("Request limit=2"):
            logs = buf.get_logs(limit=2)
            assert len(logs) == 2
            assert logs[0].message == "msg-3"
            assert logs[1].message == "msg-4"

    @autotest.num("316")
    @autotest.external_id("gns3-log-buffer-close")
    @autotest.name("LogBuffer.close: clears the buffer")
    async def test_close(self):
        with autotest.step("Add entries, then close"):
            buf = LogBuffer()
            buf._add_entry(LogLevel.INFO, "msg")
            await buf.close()

        with autotest.step("Buffer is empty"):
            assert len(buf.get_logs()) == 0
            assert buf.connected is False

    @autotest.num("317")
    @autotest.external_id("gns3-log-buffer-initial-state")
    @autotest.name("LogBuffer: initial state")
    def test_initial_state(self):
        with autotest.step("Create a buffer"):
            buf = LogBuffer(max_entries=100, inactivity_timeout=60.0)

        with autotest.step("Assert"):
            assert buf.connected is False
            assert len(buf.get_logs()) == 0
            assert len(buf.get_errors()) == 0
