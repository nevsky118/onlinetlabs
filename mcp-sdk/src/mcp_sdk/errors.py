"""Иерархия исключений MCP-сервера."""


class MCPServerError(Exception):
    """Базовая ошибка MCP-сервера."""


class TargetSystemConnectionError(MCPServerError):
    """Не удалось подключиться к целевой системе."""


class TargetSystemAPIError(MCPServerError):
    """Целевая система вернула ошибку."""

    def __init__(
        self,
        status_code: int,
        response_body: str | None = None,
        message: str | None = None,
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message or f"Target system API error: {status_code}")


class ComponentNotFoundError(MCPServerError):
    """Компонент не найден в целевой системе."""

    def __init__(self, component_id: str, message: str | None = None):
        self.component_id = component_id
        super().__init__(message or f"Component not found: {component_id}")


class ActionExecutionError(MCPServerError):
    """Ошибка выполнения действия в целевой системе."""

    def __init__(self, action_name: str, reason: str):
        self.action_name = action_name
        self.reason = reason
        super().__init__(f"Action '{action_name}' failed: {reason}")


class SessionContextError(MCPServerError):
    """Невалидный или отсутствующий контекст сессии."""
