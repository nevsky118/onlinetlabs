from datetime import datetime, timezone, timedelta

import pytest

from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.log_buffer]


class TestLogBuffer:
    @pytest.fixture
    def buffer(self):
        from src.log_buffer import LogBuffer
        return LogBuffer(max_entries=5)

    @autotests.num("360")
    @autotests.external_id("c1d2e3f4-0001-4ccc-dddd-000000000001")
    @autotests.name("GNS3 LogBuffer: добавление записей")
    def test_add_entries(self, buffer):
        from onlinetlabs_mcp_sdk.models import LogLevel

        # Act
        with autotests.step("Добавляем записи"):
            buffer._add_entry(LogLevel.INFO, "msg1")
            buffer._add_entry(LogLevel.ERROR, "err1")

        # Assert
        with autotests.step("Проверяем get_logs"):
            logs = buffer.get_logs()
            assert len(logs) == 2

    @autotests.num("361")
    @autotests.external_id("c1d2e3f4-0002-4ccc-dddd-000000000002")
    @autotests.name("GNS3 LogBuffer: ring buffer вытеснение")
    def test_ring_buffer_eviction(self, buffer):
        from onlinetlabs_mcp_sdk.models import LogLevel

        # Act
        with autotests.step("Добавляем 7 записей в буфер max=5"):
            for idx in range(7):
                buffer._add_entry(LogLevel.INFO, f"msg{idx}")

        # Assert
        with autotests.step("Проверяем что старые вытеснены"):
            logs = buffer.get_logs()
            assert len(logs) == 5
            assert logs[0].message == "msg2"

    @autotests.num("362")
    @autotests.external_id("c1d2e3f4-0003-4ccc-dddd-000000000003")
    @autotests.name("GNS3 LogBuffer: get_errors фильтрует по уровню")
    def test_get_errors_filters(self, buffer):
        from onlinetlabs_mcp_sdk.models import LogLevel

        # Arrange
        buffer._add_entry(LogLevel.INFO, "info")
        buffer._add_entry(LogLevel.ERROR, "error")
        buffer._add_entry(LogLevel.WARNING, "warning")

        # Act
        with autotests.step("Получаем ошибки"):
            errors = buffer.get_errors()

        # Assert
        with autotests.step("Только error и warning"):
            assert len(errors) == 2
            levels = {entry.level for entry in errors}
            assert LogLevel.INFO not in levels

    @autotests.num("363")
    @autotests.external_id("c1d2e3f4-0004-4ccc-dddd-000000000004")
    @autotests.name("GNS3 LogBuffer: get_errors с since")
    def test_get_errors_since(self, buffer):
        from onlinetlabs_mcp_sdk.models import LogLevel

        # Arrange
        buffer._add_entry(LogLevel.ERROR, "old error")
        since = datetime.now(tz=timezone.utc) + timedelta(seconds=1)
        buffer._add_entry(LogLevel.ERROR, "new error")

        # Act
        with autotests.step("Получаем ошибки с since (будущее)"):
            errors = buffer.get_errors(since=since)

        # Assert — only entries AFTER since
        # Обе записи создались примерно в одно время, since в будущем → 0
        with autotests.step("Нет ошибок после since"):
            assert len(errors) == 0

    @autotests.num("364")
    @autotests.external_id("c1d2e3f4-0005-4ccc-dddd-000000000005")
    @autotests.name("GNS3 LogBuffer: get_logs фильтрует по уровню")
    def test_get_logs_by_level(self, buffer):
        from onlinetlabs_mcp_sdk.models import LogLevel

        # Arrange
        buffer._add_entry(LogLevel.INFO, "info")
        buffer._add_entry(LogLevel.ERROR, "error")
        buffer._add_entry(LogLevel.INFO, "info2")

        # Act
        with autotests.step("Получаем только ERROR"):
            logs = buffer.get_logs(level=LogLevel.ERROR)

        # Assert
        with autotests.step("Один ERROR"):
            assert len(logs) == 1
            assert logs[0].level == LogLevel.ERROR

    @autotests.num("365")
    @autotests.external_id("c1d2e3f4-0006-4ccc-dddd-000000000006")
    @autotests.name("GNS3 LogBuffer: get_logs с limit")
    def test_get_logs_limit(self, buffer):
        from onlinetlabs_mcp_sdk.models import LogLevel

        # Arrange
        for idx in range(5):
            buffer._add_entry(LogLevel.INFO, f"msg{idx}")

        # Act
        with autotests.step("Получаем с limit=2"):
            logs = buffer.get_logs(limit=2)

        # Assert
        with autotests.step("Возвращает последние 2"):
            assert len(logs) == 2
            assert logs[0].message == "msg3"
            assert logs[1].message == "msg4"

    @autotests.num("366")
    @autotests.external_id("c1d2e3f4-0007-4ccc-dddd-000000000007")
    @autotests.name("GNS3 LogBuffer: close очищает буфер")
    async def test_close(self, buffer):
        from onlinetlabs_mcp_sdk.models import LogLevel

        # Arrange
        buffer._add_entry(LogLevel.INFO, "msg")

        # Act
        with autotests.step("Закрываем буфер"):
            await buffer.close()

        # Assert
        with autotests.step("Буфер пуст"):
            assert len(buffer.get_logs()) == 0
            assert buffer.connected is False
