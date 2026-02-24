from datetime import datetime, timezone

import pytest

from tests.report import autotests

pytestmark = [pytest.mark.unit]


class TestMockSessionContext:
    @autotests.num("180")
    @autotests.external_id("66ae32ba-c74f-4ce3-9044-af2c908e8ef8")
    @autotests.name("MCP SDK Testing: mock_session_context создаёт валидный контекст")
    def test_creates_valid_context(self):
        """Проверяет создание валидного контекста через mock_session_context."""

        # Arrange
        from onlinetlabs_mcp_sdk.testing import mock_session_context

        # Act
        with autotests.step("Создаём mock контекст"):
            ctx = mock_session_context()

        # Assert
        with autotests.step("Проверяем обязательные поля"):
            assert ctx.user_id
            assert ctx.session_id
            assert ctx.environment_url

    @autotests.num("181")
    @autotests.external_id("f6b45cb4-09a6-4211-8280-997e1d5d0800")
    @autotests.name("MCP SDK Testing: mock_session_context принимает переопределения")
    def test_overrides(self):
        """Проверяет переопределение полей в mock_session_context."""

        # Arrange
        from onlinetlabs_mcp_sdk.testing import mock_session_context

        # Act
        with autotests.step("Создаём mock контекст с переопределениями"):
            ctx = mock_session_context(user_id="custom-user", project_id="proj-1")

        # Assert
        with autotests.step("Проверяем переопределённые поля"):
            assert ctx.user_id == "custom-user"
            assert ctx.project_id == "proj-1"


class TestAssertValidComponent:
    @autotests.num("182")
    @autotests.external_id("1f3e40cd-da82-4098-9e59-dbda664dec93")
    @autotests.name("MCP SDK Testing: assert_valid_component для валидного Component")
    def test_valid_component_passes(self):
        """Проверяет что assert_valid_component проходит для валидного Component."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import Component
        from onlinetlabs_mcp_sdk.testing import assert_valid_component

        # Act
        with autotests.step("Создаём валидный Component"):
            c = Component(
                id="1", name="R1", type="router", status="running", summary="ok"
            )

        # Assert
        with autotests.step("Проверяем валидность"):
            assert_valid_component(c)

    @autotests.num("183")
    @autotests.external_id("0a3f5153-eb4e-4ae9-bb16-2160e1aa9d50")
    @autotests.name(
        "MCP SDK Testing: assert_valid_component падает для невалидных данных"
    )
    def test_invalid_data_fails(self):
        """Проверяет AssertionError для невалидных данных."""

        # Arrange
        from onlinetlabs_mcp_sdk.testing import assert_valid_component

        # Act & Assert
        with autotests.step("Передаём невалидные данные"):
            with pytest.raises(AssertionError):
                assert_valid_component({"id": "1"})


class TestAssertValidErrorEntry:
    @autotests.num("184")
    @autotests.external_id("c2ad5c61-5f53-4def-9c0e-f8181c3d6238")
    @autotests.name(
        "MCP SDK Testing: assert_valid_error_entry для валидного ErrorEntry"
    )
    def test_valid_entry_passes(self):
        """Проверяет что assert_valid_error_entry проходит для валидного ErrorEntry."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import ErrorEntry, LogLevel
        from onlinetlabs_mcp_sdk.testing import assert_valid_error_entry

        # Act
        with autotests.step("Создаём валидный ErrorEntry"):
            e = ErrorEntry(
                timestamp=datetime.now(tz=timezone.utc),
                level=LogLevel.ERROR,
                message="fail",
            )

        # Assert
        with autotests.step("Проверяем валидность"):
            assert_valid_error_entry(e)


class TestFakeConnectionPool:
    @autotests.num("185")
    @autotests.external_id("42126fe8-99eb-4785-bf17-718468d1deee")
    @autotests.name("MCP SDK Testing: FakeConnectionPool возвращает соединение")
    async def test_get_connection(self):
        """Проверяет получение соединения из FakeConnectionPool."""

        # Arrange
        from onlinetlabs_mcp_sdk.testing import FakeConnectionPool

        pool = FakeConnectionPool()

        # Act
        with autotests.step("Получаем соединение"):
            conn = await pool.get_connection("http://localhost")

        # Assert
        with autotests.step("Проверяем URL"):
            assert conn["url"] == "http://localhost"

    @autotests.num("186")
    @autotests.external_id("eb9afcdc-e799-42d1-8cdd-b20e10959872")
    @autotests.name("MCP SDK Testing: FakeConnectionPool.close очищает соединения")
    async def test_close(self):
        """Проверяет что close очищает словарь соединений."""

        # Arrange
        from onlinetlabs_mcp_sdk.testing import FakeConnectionPool

        pool = FakeConnectionPool()
        await pool.get_connection("http://localhost")

        # Act
        with autotests.step("Закрываем пул"):
            await pool.close()

        # Assert
        with autotests.step("Проверяем что соединения очищены"):
            assert pool.connections == {}
