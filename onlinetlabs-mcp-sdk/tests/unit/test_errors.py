import pytest

from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.models]


class TestErrorHierarchy:
    @autotests.num("130")
    @autotests.external_id("f4cfefa3-34f2-4680-8b86-b279fbc71171")
    @autotests.name("MCP SDK Errors: базовая ошибка MCPServerError")
    def test_base_error(self):
        """Проверяет что MCPServerError можно выбросить и поймать."""

        # Arrange
        from onlinetlabs_mcp_sdk.errors import MCPServerError

        # Act & Assert
        with autotests.step("Выбрасываем MCPServerError"):
            with pytest.raises(MCPServerError):
                raise MCPServerError("test")

    @autotests.num("131")
    @autotests.external_id("78eddde5-9fea-4f45-8006-7dc18bf9f729")
    @autotests.name(
        "MCP SDK Errors: TargetSystemConnectionError наследует MCPServerError"
    )
    def test_connection_error_is_mcp_error(self):
        """Проверяет наследование TargetSystemConnectionError от MCPServerError."""

        # Arrange
        from onlinetlabs_mcp_sdk.errors import (
            MCPServerError,
            TargetSystemConnectionError,
        )

        # Act & Assert
        with autotests.step("Выбрасываем TargetSystemConnectionError"):
            with pytest.raises(MCPServerError):
                raise TargetSystemConnectionError("host unreachable")

    @autotests.num("132")
    @autotests.external_id("3add35f7-7cf9-46a1-a43b-e8db1bcb83ea")
    @autotests.name("MCP SDK Errors: атрибуты TargetSystemAPIError")
    def test_api_error_attributes(self):
        """Проверяет атрибуты status_code и response_body."""

        # Arrange
        from onlinetlabs_mcp_sdk.errors import TargetSystemAPIError

        # Act
        with autotests.step("Создаём TargetSystemAPIError"):
            err = TargetSystemAPIError(
                status_code=500, response_body='{"error": "internal"}'
            )

        # Assert
        with autotests.step("Проверяем атрибуты"):
            assert err.status_code == 500
            assert err.response_body is not None

    @autotests.num("133")
    @autotests.external_id("3f90abc4-41cc-4ac8-a884-859d6d89f35a")
    @autotests.name("MCP SDK Errors: ComponentNotFoundError хранит component_id")
    def test_component_not_found(self):
        """Проверяет что ComponentNotFoundError хранит component_id."""

        # Arrange
        from onlinetlabs_mcp_sdk.errors import ComponentNotFoundError

        # Act
        with autotests.step("Создаём ComponentNotFoundError"):
            err = ComponentNotFoundError(component_id="node-99")

        # Assert
        with autotests.step("Проверяем component_id"):
            assert err.component_id == "node-99"

    @autotests.num("134")
    @autotests.external_id("0a50a6d5-2ce3-49b9-8d63-fc4e6dd82f6e")
    @autotests.name("MCP SDK Errors: ActionExecutionError хранит action_name и reason")
    def test_action_execution_error(self):
        """Проверяет атрибуты ActionExecutionError."""

        # Arrange
        from onlinetlabs_mcp_sdk.errors import ActionExecutionError

        # Act
        with autotests.step("Создаём ActionExecutionError"):
            err = ActionExecutionError(action_name="restart", reason="node is locked")

        # Assert
        with autotests.step("Проверяем атрибуты"):
            assert err.action_name == "restart"
            assert "locked" in err.reason

    @autotests.num("135")
    @autotests.external_id("fe198f08-ebd9-4858-a7cc-99e52238409d")
    @autotests.name("MCP SDK Errors: SessionContextError наследует MCPServerError")
    def test_session_context_error(self):
        """Проверяет наследование SessionContextError от MCPServerError."""

        # Arrange
        from onlinetlabs_mcp_sdk.errors import MCPServerError, SessionContextError

        # Act & Assert
        with autotests.step("Выбрасываем SessionContextError"):
            with pytest.raises(MCPServerError):
                raise SessionContextError("missing user_id")
