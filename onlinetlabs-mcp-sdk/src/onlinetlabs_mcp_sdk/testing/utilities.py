"""Утилиты тестирования для MCP-серверов."""

from typing import Any

from onlinetlabs_mcp_sdk.context import SessionContext
from onlinetlabs_mcp_sdk.models import Component, ErrorEntry


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
    assert isinstance(obj, Component), f"Expected Component, got {type(obj).__name__}"
    assert obj.id, "Component.id must not be empty"
    assert obj.name, "Component.name must not be empty"
    assert obj.type, "Component.type must not be empty"
    assert obj.status, "Component.status must not be empty"


def assert_valid_error_entry(obj: Any) -> None:
    """Проверить что объект — валидный ErrorEntry."""
    assert isinstance(obj, ErrorEntry), f"Expected ErrorEntry, got {type(obj).__name__}"
    assert obj.timestamp is not None, "ErrorEntry.timestamp must not be None"
    assert obj.message, "ErrorEntry.message must not be empty"


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
