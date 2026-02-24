import pytest

from tests.report import autotests

pytestmark = [pytest.mark.smoke]


class TestPublicAPI:
    @autotests.num("200")
    @autotests.external_id("afd527cc-90c5-46f1-b1e0-b443c244e8b7")
    @autotests.name("MCP SDK API: протоколы импортируемы")
    def test_protocols_importable(self):
        """Проверяет импорт протоколов из публичного API."""

        # Act & Assert
        with autotests.step("Импортируем протоколы"):
            from onlinetlabs_mcp_sdk import (  # noqa: F401
                ActionProvider,
                HistoryProvider,
                LogProvider,
                StateProvider,
            )

    @autotests.num("201")
    @autotests.external_id("a342c33e-90de-4008-8966-1d88c3ce0163")
    @autotests.name("MCP SDK API: модели импортируемы")
    def test_models_importable(self):
        """Проверяет импорт моделей из публичного API."""

        # Act & Assert
        with autotests.step("Импортируем модели"):
            from onlinetlabs_mcp_sdk import (  # noqa: F401
                ActionResult,
                ActionSpec,
                Component,
                ComponentDetail,
                ErrorEntry,
                LogEntry,
                LogLevel,
                SystemOverview,
                UserAction,
            )

    @autotests.num("202")
    @autotests.external_id("025ef830-5930-4dc0-9d42-83a9f4e6dc4f")
    @autotests.name("MCP SDK API: сервер импортируем")
    def test_server_importable(self):
        """Проверяет импорт OnlinetlabsMCPServer."""

        # Act & Assert
        with autotests.step("Импортируем сервер"):
            from onlinetlabs_mcp_sdk import OnlinetlabsMCPServer  # noqa: F401

    @autotests.num("203")
    @autotests.external_id("44c79523-8262-41ea-aa2c-2e8d6f33c22f")
    @autotests.name("MCP SDK API: контекст импортируем")
    def test_context_importable(self):
        """Проверяет импорт SessionContext и ServerCapabilities."""

        # Act & Assert
        with autotests.step("Импортируем контекст"):
            from onlinetlabs_mcp_sdk import (  # noqa: F401
                ServerCapabilities,
                SessionContext,
            )

    @autotests.num("204")
    @autotests.external_id("ffae3aeb-35fb-46e7-8f82-ec2dfd86c5a9")
    @autotests.name("MCP SDK API: ошибки импортируемы")
    def test_errors_importable(self):
        """Проверяет импорт ошибок из публичного API."""

        # Act & Assert
        with autotests.step("Импортируем ошибки"):
            from onlinetlabs_mcp_sdk import (  # noqa: F401
                ActionExecutionError,
                ComponentNotFoundError,
                MCPServerError,
                SessionContextError,
                TargetSystemAPIError,
                TargetSystemConnectionError,
            )

    @autotests.num("205")
    @autotests.external_id("2b20cefb-6fa6-4488-ab25-37fa70fb7970")
    @autotests.name("MCP SDK API: connection импортируем")
    def test_connection_importable(self):
        """Проверяет импорт BaseConnectionManager и ConnectionPool."""

        # Act & Assert
        with autotests.step("Импортируем connection"):
            from onlinetlabs_mcp_sdk import (  # noqa: F401
                BaseConnectionManager,
                ConnectionPool,
            )

    @autotests.num("206")
    @autotests.external_id("e470df87-8eb4-4c6b-a2c0-a3fdfb361adb")
    @autotests.name("MCP SDK API: transport импортируем")
    def test_transport_importable(self):
        """Проверяет импорт TransportConfig."""

        # Act & Assert
        with autotests.step("Импортируем transport"):
            from onlinetlabs_mcp_sdk import TransportConfig  # noqa: F401

    @autotests.num("207")
    @autotests.external_id("4a2898d9-4234-4d29-a782-854ebd4e7783")
    @autotests.name("MCP SDK API: модели аутентификации импортируемы")
    def test_auth_models_importable(self):
        """Проверяет импорт моделей аутентификации."""

        # Act & Assert
        with autotests.step("Импортируем модели аутентификации"):
            from onlinetlabs_mcp_sdk import (  # noqa: F401
                APIKeyAuth,
                SocketAuth,
                TargetSystemAuth,
            )
