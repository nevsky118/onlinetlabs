"""Утилиты тестирования для MCP-серверов."""

from typing import Any

from mcp_sdk.context import SessionContext
from mcp_sdk.models import Component, ErrorEntry
from mcp_sdk.testing.custom_assertions import assert_is_instance, assert_is_not_none, assert_true


def mock_session_context(**overrides: Any) -> SessionContext:
    """Создать тестовый SessionContext с разумными значениями по умолчанию."""
    defaults = {
        "user_id": "test-user",
        "session_id": "test-session",
        "environment_url": "http://localhost:3080",
    }
    defaults.update(overrides)
    return SessionContext(**defaults)


def assert_valid_component(obj: Any) -> None:
    """Проверить что объект — валидный Component."""
    assert_is_instance(obj, Component, f"Expected Component, got {type(obj).__name__}")
    assert_true(obj.id, "Component.id must not be empty")
    assert_true(obj.name, "Component.name must not be empty")
    assert_true(obj.type, "Component.type must not be empty")
    assert_true(obj.status, "Component.status must not be empty")


def assert_valid_error_entry(obj: Any) -> None:
    """Проверить что объект — валидный ErrorEntry."""
    assert_is_instance(obj, ErrorEntry, f"Expected ErrorEntry, got {type(obj).__name__}")
    assert_is_not_none(obj.timestamp, "ErrorEntry.timestamp must not be None")
    assert_true(obj.message, "ErrorEntry.message must not be empty")


class FakeConnectionPool:
    """Мок пула подключений для тестов."""

    def __init__(self) -> None:
        self.connections: dict[str, dict] = {}

    async def get_connection(self, environment_url: str) -> dict:
        if environment_url not in self.connections:
            self.connections[environment_url] = {"url": environment_url}
        return self.connections[environment_url]

    async def close(self) -> None:
        self.connections.clear()
