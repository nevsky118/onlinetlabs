import pytest
from mcp.server.fastmcp import FastMCP

from tests.helpers.fakes import (
    FakeActionProvider,
    FakeAllProtocols,
    FakeErrorAllProtocols,
    FakeErrorStateProvider,
    FakeHistoryProvider,
    FakeLogProvider,
    FakeMCPErrorAllProtocols,
    FakeStateProvider,
    MCPErrorProvider,
)
from tests.report import autotests

from onlinetlabs_mcp_sdk.errors import MCPServerError, SessionContextError
from onlinetlabs_mcp_sdk.server import OnlinetlabsMCPServer

pytestmark = [pytest.mark.integration, pytest.mark.server]

VALID_CTX = {
    "user_id": "u1",
    "session_id": "s1",
    "environment_url": "http://localhost:3080",
}


def _get_tool_fn(server: OnlinetlabsMCPServer, name: str):
    """Extract raw async tool function from FastMCP internal registry."""
    return server.mcp._tool_manager._tools[name].fn


class FakeNoState:
    pass


# ---------------------------------------------------------------
# Builder / registration tests (existing)
# ---------------------------------------------------------------


class TestServerBuilder:
    @autotests.num("170")
    @autotests.external_id("b35ad774-7a9b-4ef9-a6e8-d88c589945fd")
    @autotests.name("MCP SDK Server: создание сервера с StateProvider")
    def test_create_with_state_provider(self):
        """Проверяет создание сервера с StateProvider."""

        # Arrange & Act
        with autotests.step("Создаём сервер с FakeStateProvider"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())

        # Assert
        with autotests.step("Проверяем capabilities"):
            assert "state" in server.capabilities

    @autotests.num("171")
    @autotests.external_id("89da7500-681e-4939-8552-f90a6f57e8b3")
    @autotests.name("MCP SDK Server: создание сервера с StateProvider и LogProvider")
    def test_create_with_state_and_logs(self):
        """Проверяет создание сервера с StateProvider и LogProvider."""

        # Arrange & Act
        with autotests.step("Создаём сервер с FakeLogProvider"):
            server = OnlinetlabsMCPServer("test", FakeLogProvider())

        # Assert
        with autotests.step("Проверяем capabilities"):
            assert "state" in server.capabilities
            assert "logs" in server.capabilities

    @autotests.num("172")
    @autotests.external_id("81f69969-128d-43cd-95ad-bf6a524625f9")
    @autotests.name("MCP SDK Server: ошибка валидации без StateProvider")
    def test_validation_fails_without_state(self):
        """Проверяет ошибку при отсутствии StateProvider."""

        # Act & Assert
        with autotests.step("Создаём сервер без StateProvider"):
            with pytest.raises(ValueError, match="StateProvider"):
                OnlinetlabsMCPServer("test", FakeNoState())

    @autotests.num("173")
    @autotests.external_id("31f7dc17-1f0a-4ff7-acfb-d935b27bbb56")
    @autotests.name("MCP SDK Server: зарегистрированные инструменты включают state")
    def test_registered_tools_include_state(self):
        """Проверяет регистрацию state-инструментов."""

        # Arrange & Act
        with autotests.step("Создаём сервер и получаем tool_names"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())
            tool_names = server.tool_names

        # Assert
        with autotests.step("Проверяем наличие state-инструментов"):
            assert "list_components" in tool_names
            assert "get_component" in tool_names
            assert "get_system_overview" in tool_names

    @autotests.num("174")
    @autotests.external_id("8f38443d-4d62-4e50-a5d2-598c895328df")
    @autotests.name("MCP SDK Server: зарегистрированные инструменты включают logs")
    def test_registered_tools_include_logs(self):
        """Проверяет регистрацию log-инструментов."""

        # Arrange & Act
        with autotests.step("Создаём сервер с логами"):
            server = OnlinetlabsMCPServer("test", FakeLogProvider())

        # Assert
        with autotests.step("Проверяем наличие log-инструментов"):
            assert "list_errors" in server.tool_names
            assert "get_logs" in server.tool_names

    @autotests.num("175")
    @autotests.external_id("1fd5f4c3-6bb7-4014-8c34-b337b1174603")
    @autotests.name(
        "MCP SDK Server: log-инструменты не зарегистрированы без LogProvider"
    )
    def test_logs_not_registered_without_provider(self):
        """Проверяет отсутствие log-инструментов без LogProvider."""

        # Arrange & Act
        with autotests.step("Создаём сервер без LogProvider"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())

        # Assert
        with autotests.step("Проверяем отсутствие log-инструментов"):
            assert "list_errors" not in server.tool_names

    @autotests.num("176")
    @autotests.external_id("ab39f4d3-4d8f-4d4e-bea1-40f9b37cc294")
    @autotests.name("MCP SDK Server: get_capabilities зарегистрирован")
    def test_get_capabilities_tool_registered(self):
        """Проверяет регистрацию get_capabilities."""

        # Arrange & Act
        with autotests.step("Создаём сервер"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())

        # Assert
        with autotests.step("Проверяем наличие get_capabilities"):
            assert "get_capabilities" in server.tool_names

    @autotests.num("177")
    @autotests.external_id("9ecd2c69-1df1-408d-8f72-30a9df85dcf3")
    @autotests.name("MCP SDK Server: регистрация доменного инструмента")
    def test_domain_tool_registration(self):
        """Проверяет регистрацию доменного инструмента через декоратор."""

        # Arrange
        server = OnlinetlabsMCPServer("test", FakeStateProvider())

        # Act
        with autotests.step("Регистрируем доменный инструмент"):

            @server.domain_tool(description="Тестовый доменный инструмент")
            async def custom_tool(param: str) -> str:
                return param

        # Assert
        with autotests.step("Проверяем наличие custom_tool"):
            assert "custom_tool" in server.tool_names


# ---------------------------------------------------------------
# Tool execution tests
# ---------------------------------------------------------------


class TestServerToolExecution:
    @autotests.num("178")
    @autotests.external_id("a3c1e7f2-4b6d-4a8e-9c3f-1d5e7b9a2c4d")
    @autotests.name("MCP SDK Server: list_components возвращает список компонентов")
    async def test_list_components_tool(self):
        """Вызов list_components через FastMCP возвращает list[dict]."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())
            fn = _get_tool_fn(server, "list_components")

        # Act
        with autotests.step("Call list_components tool"):
            result = await fn(ctx=VALID_CTX)

        # Assert
        with autotests.step("Verify result contains component data"):
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "n1"
            assert result[0]["type"] == "router"

    @autotests.num("179")
    @autotests.external_id("b4d2f8a3-5c7e-4b9f-ad40-2e6f8c0b3d5e")
    @autotests.name("MCP SDK Server: get_component возвращает детали компонента")
    async def test_get_component_tool(self):
        """Вызов get_component возвращает dict с деталями."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())
            fn = _get_tool_fn(server, "get_component")

        # Act
        with autotests.step("Call get_component tool"):
            result = await fn(ctx=VALID_CTX, component_id="n1")

        # Assert
        with autotests.step("Verify component details"):
            assert isinstance(result, dict)
            assert result["id"] == "n1"
            assert "properties" in result

    @autotests.num("180")
    @autotests.external_id("c5e3a9b4-6d8f-4c0a-be51-3f7a9d1c4e6f")
    @autotests.name("MCP SDK Server: get_system_overview возвращает обзор системы")
    async def test_get_system_overview_tool(self):
        """Вызов get_system_overview возвращает dict с обзором."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())
            fn = _get_tool_fn(server, "get_system_overview")

        # Act
        with autotests.step("Call get_system_overview tool"):
            result = await fn(ctx=VALID_CTX)

        # Assert
        with autotests.step("Verify system overview data"):
            assert isinstance(result, dict)
            assert result["system_name"] == "fake"
            assert result["component_count"] == 1

    @autotests.num("181")
    @autotests.external_id("d6f4ba05-7e9a-4d1b-cf62-4a8b0e2d5f7a")
    @autotests.name("MCP SDK Server: list_errors возвращает записи об ошибках")
    async def test_list_errors_tool(self):
        """Вызов list_errors возвращает list[dict] с ошибками."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeLogProvider())
            fn = _get_tool_fn(server, "list_errors")

        # Act
        with autotests.step("Call list_errors tool"):
            result = await fn(ctx=VALID_CTX)

        # Assert
        with autotests.step("Verify error entries"):
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["level"] == "error"
            assert result[0]["message"] == "Link down"

    @autotests.num("182")
    @autotests.external_id("e7a5cb16-8fab-4e2c-da73-5b9c1f3e6a8b")
    @autotests.name("MCP SDK Server: get_logs фильтрует по уровню")
    async def test_get_logs_tool(self):
        """Вызов get_logs с level='info' возвращает записи логов."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeLogProvider())
            fn = _get_tool_fn(server, "get_logs")

        # Act
        with autotests.step("Call get_logs tool with level=info"):
            result = await fn(ctx=VALID_CTX, level="info", limit=50)

        # Assert
        with autotests.step("Verify log entries"):
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["level"] == "info"

    @autotests.num("183")
    @autotests.external_id("f8b6dc27-9abc-4f3d-eb84-6c0d2a4f7b9c")
    @autotests.name("MCP SDK Server: list_user_actions возвращает действия")
    async def test_list_user_actions_tool(self):
        """Вызов list_user_actions возвращает list[dict]."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeHistoryProvider())
            fn = _get_tool_fn(server, "list_user_actions")

        # Act
        with autotests.step("Call list_user_actions tool"):
            result = await fn(ctx=VALID_CTX, limit=10)

        # Assert
        with autotests.step("Verify user action entries"):
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["action"] == "configure"
            assert result[0]["success"] is True

    @autotests.num("184")
    @autotests.external_id("a9c7ed38-0bcd-4a4e-fc95-7d1e3b5a8c0d")
    @autotests.name("MCP SDK Server: list_available_actions возвращает спецификации")
    async def test_list_available_actions_tool(self):
        """Вызов list_available_actions возвращает list[dict]."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeActionProvider())
            fn = _get_tool_fn(server, "list_available_actions")

        # Act
        with autotests.step("Call list_available_actions tool"):
            result = await fn(ctx=VALID_CTX)

        # Assert
        with autotests.step("Verify action specs"):
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["name"] == "restart_node"

    @autotests.num("185")
    @autotests.external_id("b0d8fe49-1cde-4b5f-ad06-8e2f4c6b9d1e")
    @autotests.name("MCP SDK Server: execute_action выполняет действие")
    async def test_execute_action_tool(self):
        """Вызов execute_action возвращает результат."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeActionProvider())
            fn = _get_tool_fn(server, "execute_action")

        # Act
        with autotests.step("Call execute_action tool"):
            result = await fn(
                ctx=VALID_CTX, action_name="restart_node", params={"node_id": "n1"}
            )

        # Assert
        with autotests.step("Verify action result"):
            assert isinstance(result, dict)
            assert result["success"] is True
            assert "restart_node" in result["message"]

    @autotests.num("186")
    @autotests.external_id("c1e9af5a-2def-4c6a-be17-9f3a5d7c0e2f")
    @autotests.name("MCP SDK Server: get_capabilities возвращает все 4 capability")
    async def test_get_capabilities_tool(self):
        """Вызов get_capabilities для FakeAllProtocols возвращает все capability."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeAllProtocols())
            fn = _get_tool_fn(server, "get_capabilities")

        # Act
        with autotests.step("Call get_capabilities tool"):
            result = await fn()

        # Assert
        with autotests.step("Verify all 4 capabilities present"):
            assert isinstance(result, dict)
            assert result["system_name"] == "test"
            assert sorted(result["capabilities"]) == [
                "actions",
                "history",
                "logs",
                "state",
            ]

    @autotests.num("187")
    @autotests.external_id("d2fa0b6b-3ef0-4d7b-cf28-0a4b6e8d1f3a")
    @autotests.name("MCP SDK Server: невалидный ctx вызывает SessionContextError")
    async def test_invalid_context_raises(self):
        """Пустой ctx вызывает SessionContextError."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())
            fn = _get_tool_fn(server, "list_components")

        # Act & Assert
        with autotests.step("Verify SessionContextError on empty ctx"):
            with pytest.raises(SessionContextError, match="Invalid session context"):
                await fn(ctx={})

    @autotests.num("188")
    @autotests.external_id("e3ab1c7c-4fa1-4e8c-da39-1b5c7f9e2a4b")
    @autotests.name("MCP SDK Server: неожиданная ошибка оборачивается в MCPServerError")
    async def test_unexpected_error_wrapped(self):
        """RuntimeError от FakeErrorStateProvider → MCPServerError."""

        # Arrange
        with autotests.step("Create server with error provider"):
            server = OnlinetlabsMCPServer("test", FakeErrorStateProvider())
            fn = _get_tool_fn(server, "list_components")

        # Act & Assert
        with autotests.step("Verify RuntimeError wrapped in MCPServerError"):
            with pytest.raises(MCPServerError, match="Internal server error"):
                await fn(ctx=VALID_CTX)

    @autotests.num("189")
    @autotests.external_id("f4bc2d8d-5ab2-4f9d-eb40-2c6d8a0f3b5c")
    @autotests.name(
        "MCP SDK Server: FakeAllProtocols регистрирует все 9 инструментов"
    )
    def test_all_protocols_register_all_tools(self):
        """Сервер с FakeAllProtocols регистрирует все 9 инструментов."""

        # Arrange & Act
        with autotests.step("Create server with all protocols"):
            server = OnlinetlabsMCPServer("test", FakeAllProtocols())

        # Assert
        with autotests.step("Verify all 9 tools registered"):
            expected = {
                "list_components",
                "get_component",
                "get_system_overview",
                "list_errors",
                "get_logs",
                "list_user_actions",
                "list_available_actions",
                "execute_action",
                "get_capabilities",
            }
            assert set(server.tool_names) == expected

    @autotests.num("190")
    @autotests.external_id("a5cd3e9e-6bc3-4a0e-fc51-3d7e9b1a4c6d")
    @autotests.name(
        "MCP SDK Server: history/action инструменты не зарегистрированы без провайдеров"
    )
    def test_history_action_not_registered(self):
        """Сервер с FakeStateProvider не регистрирует history/action инструменты."""

        # Arrange & Act
        with autotests.step("Create server with state provider only"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())

        # Assert
        with autotests.step("Verify history/action tools absent"):
            assert "list_user_actions" not in server.tool_names
            assert "list_available_actions" not in server.tool_names
            assert "execute_action" not in server.tool_names

    @autotests.num("191")
    @autotests.external_id("b6de4f0f-7cd4-4b1f-ad62-4e8f0c2b5d7e")
    @autotests.name("MCP SDK Server: свойство mcp возвращает FastMCP")
    def test_mcp_property(self):
        """server.mcp — экземпляр FastMCP."""

        # Arrange & Act
        with autotests.step("Create server"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())

        # Assert
        with autotests.step("Verify mcp is FastMCP instance"):
            assert isinstance(server.mcp, FastMCP)

    @autotests.num("192")
    @autotests.external_id("c7ef5a10-8de5-4c2a-be73-5f9a1d3c6e8f")
    @autotests.name("MCP SDK Server: list_errors с параметром since")
    async def test_list_errors_with_since(self):
        """Вызов list_errors с ISO datetime строкой since."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeLogProvider())
            fn = _get_tool_fn(server, "list_errors")

        # Act
        with autotests.step("Call list_errors with since parameter"):
            result = await fn(ctx=VALID_CTX, since="2024-01-01T00:00:00+00:00")

        # Assert
        with autotests.step("Verify result is a list"):
            assert isinstance(result, list)

    @autotests.num("193")
    @autotests.external_id("d8fa6b21-9ef6-4d3b-cf84-6a0b2e4d7f9a")
    @autotests.name("MCP SDK Server: list_available_actions с component_id")
    async def test_list_available_actions_with_component_id(self):
        """Вызов list_available_actions с component_id."""

        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeActionProvider())
            fn = _get_tool_fn(server, "list_available_actions")

        # Act
        with autotests.step("Call list_available_actions with component_id"):
            result = await fn(ctx=VALID_CTX, component_id="n1")

        # Assert
        with autotests.step("Verify result is a list"):
            assert isinstance(result, list)

    @autotests.num("194")
    @autotests.external_id("e9ab7c32-0fa7-4e4c-da95-7b1c3f5e8a0b")
    @autotests.name("MCP SDK Server: MCPServerError проходит через re-raise")
    async def test_mcp_server_error_passthrough(self):
        """MCPServerError от реализации не оборачивается повторно."""

        # Arrange
        with autotests.step("Create server with MCPErrorProvider"):
            server = OnlinetlabsMCPServer("test", MCPErrorProvider())
            fn = _get_tool_fn(server, "list_components")

        # Act & Assert
        with autotests.step("Verify MCPServerError passes through"):
            with pytest.raises(MCPServerError, match="Custom MCP error"):
                await fn(ctx=VALID_CTX)

    @autotests.num("195")
    @autotests.external_id("fa0c8d43-1ab8-4f5d-eb06-8c2d4a6f9b1c")
    @autotests.name("MCP SDK Server: run вызывает FastMCP.run")
    def test_run_delegates_to_fastmcp(self, monkeypatch):
        """server.run() делегирует вызов в FastMCP.run()."""

        # Arrange
        with autotests.step("Create server and mock FastMCP.run"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())
            called_with = {}

            def fake_run(*, transport, **kwargs):
                called_with["transport"] = transport
                called_with.update(kwargs)

            monkeypatch.setattr(server.mcp, "run", fake_run)

        # Act
        with autotests.step("Call server.run"):
            server.run(transport="stdio")

        # Assert
        with autotests.step("Verify delegation to FastMCP.run"):
            assert called_with["transport"] == "stdio"


# ---------------------------------------------------------------
# Error handling per-tool tests (SessionContextError, MCPServerError, Exception)
# ---------------------------------------------------------------


class TestServerErrorHandling:
    """Tests error handling branches in every tool function."""

    # -- Invalid ctx → SessionContextError for each tool --------

    @autotests.num("196")
    @autotests.external_id("a1b2c3d4-1111-4aaa-bbbb-111111111111")
    @autotests.name("MCP SDK Server: get_component с невалидным ctx")
    async def test_get_component_invalid_ctx(self):
        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())
            fn = _get_tool_fn(server, "get_component")

        # Act & Assert
        with autotests.step("Verify SessionContextError on empty ctx"):
            with pytest.raises(SessionContextError):
                await fn(ctx={}, component_id="n1")

    @autotests.num("197")
    @autotests.external_id("a1b2c3d4-2222-4aaa-bbbb-222222222222")
    @autotests.name("MCP SDK Server: get_system_overview с невалидным ctx")
    async def test_get_system_overview_invalid_ctx(self):
        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeStateProvider())
            fn = _get_tool_fn(server, "get_system_overview")

        # Act & Assert
        with autotests.step("Verify SessionContextError on empty ctx"):
            with pytest.raises(SessionContextError):
                await fn(ctx={})

    @autotests.num("198")
    @autotests.external_id("a1b2c3d4-3333-4aaa-bbbb-333333333333")
    @autotests.name("MCP SDK Server: list_errors с невалидным ctx")
    async def test_list_errors_invalid_ctx(self):
        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeLogProvider())
            fn = _get_tool_fn(server, "list_errors")

        # Act & Assert
        with autotests.step("Verify SessionContextError on empty ctx"):
            with pytest.raises(SessionContextError):
                await fn(ctx={})

    @autotests.num("199")
    @autotests.external_id("a1b2c3d4-4444-4aaa-bbbb-444444444444")
    @autotests.name("MCP SDK Server: get_logs с невалидным ctx")
    async def test_get_logs_invalid_ctx(self):
        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeLogProvider())
            fn = _get_tool_fn(server, "get_logs")

        # Act & Assert
        with autotests.step("Verify SessionContextError on empty ctx"):
            with pytest.raises(SessionContextError):
                await fn(ctx={})

    @autotests.num("200")
    @autotests.external_id("a1b2c3d4-5555-4aaa-bbbb-555555555555")
    @autotests.name("MCP SDK Server: list_user_actions с невалидным ctx")
    async def test_list_user_actions_invalid_ctx(self):
        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeHistoryProvider())
            fn = _get_tool_fn(server, "list_user_actions")

        # Act & Assert
        with autotests.step("Verify SessionContextError on empty ctx"):
            with pytest.raises(SessionContextError):
                await fn(ctx={})

    @autotests.num("201")
    @autotests.external_id("a1b2c3d4-6666-4aaa-bbbb-666666666666")
    @autotests.name("MCP SDK Server: list_available_actions с невалидным ctx")
    async def test_list_available_actions_invalid_ctx(self):
        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeActionProvider())
            fn = _get_tool_fn(server, "list_available_actions")

        # Act & Assert
        with autotests.step("Verify SessionContextError on empty ctx"):
            with pytest.raises(SessionContextError):
                await fn(ctx={})

    @autotests.num("202")
    @autotests.external_id("a1b2c3d4-7777-4aaa-bbbb-777777777777")
    @autotests.name("MCP SDK Server: execute_action с невалидным ctx")
    async def test_execute_action_invalid_ctx(self):
        # Arrange
        with autotests.step("Create server and get tool function"):
            server = OnlinetlabsMCPServer("test", FakeActionProvider())
            fn = _get_tool_fn(server, "execute_action")

        # Act & Assert
        with autotests.step("Verify SessionContextError on empty ctx"):
            with pytest.raises(SessionContextError):
                await fn(ctx={}, action_name="restart", params={})

    # -- Unexpected error → MCPServerError for each tool --------

    @autotests.num("203")
    @autotests.external_id("b2c3d4e5-1111-4bbb-cccc-111111111111")
    @autotests.name("MCP SDK Server: get_component unexpected error → MCPServerError")
    async def test_get_component_unexpected_error(self):
        # Arrange
        with autotests.step("Create server with error provider"):
            server = OnlinetlabsMCPServer("test", FakeErrorStateProvider())
            fn = _get_tool_fn(server, "get_component")

        # Act & Assert
        with autotests.step("Verify unexpected error wrapped in MCPServerError"):
            with pytest.raises(MCPServerError, match="Internal server error"):
                await fn(ctx=VALID_CTX, component_id="n1")

    @autotests.num("204")
    @autotests.external_id("b2c3d4e5-2222-4bbb-cccc-222222222222")
    @autotests.name("MCP SDK Server: get_system_overview unexpected error → MCPServerError")
    async def test_get_system_overview_unexpected_error(self):
        # Arrange
        with autotests.step("Create server with error provider"):
            server = OnlinetlabsMCPServer("test", FakeErrorStateProvider())
            fn = _get_tool_fn(server, "get_system_overview")

        # Act & Assert
        with autotests.step("Verify unexpected error wrapped in MCPServerError"):
            with pytest.raises(MCPServerError, match="Internal server error"):
                await fn(ctx=VALID_CTX)

    @autotests.num("205")
    @autotests.external_id("b2c3d4e5-3333-4bbb-cccc-333333333333")
    @autotests.name("MCP SDK Server: list_errors unexpected error → MCPServerError")
    async def test_list_errors_unexpected_error(self):
        # Arrange
        with autotests.step("Create server with error provider"):
            server = OnlinetlabsMCPServer("test", FakeErrorAllProtocols())
            fn = _get_tool_fn(server, "list_errors")

        # Act & Assert
        with autotests.step("Verify unexpected error wrapped in MCPServerError"):
            with pytest.raises(MCPServerError, match="Internal server error"):
                await fn(ctx=VALID_CTX)

    @autotests.num("206")
    @autotests.external_id("b2c3d4e5-4444-4bbb-cccc-444444444444")
    @autotests.name("MCP SDK Server: get_logs unexpected error → MCPServerError")
    async def test_get_logs_unexpected_error(self):
        # Arrange
        with autotests.step("Create server with error provider"):
            server = OnlinetlabsMCPServer("test", FakeErrorAllProtocols())
            fn = _get_tool_fn(server, "get_logs")

        # Act & Assert
        with autotests.step("Verify unexpected error wrapped in MCPServerError"):
            with pytest.raises(MCPServerError, match="Internal server error"):
                await fn(ctx=VALID_CTX)

    @autotests.num("207")
    @autotests.external_id("b2c3d4e5-5555-4bbb-cccc-555555555555")
    @autotests.name("MCP SDK Server: list_user_actions unexpected error → MCPServerError")
    async def test_list_user_actions_unexpected_error(self):
        # Arrange
        with autotests.step("Create server with error provider"):
            server = OnlinetlabsMCPServer("test", FakeErrorAllProtocols())
            fn = _get_tool_fn(server, "list_user_actions")

        # Act & Assert
        with autotests.step("Verify unexpected error wrapped in MCPServerError"):
            with pytest.raises(MCPServerError, match="Internal server error"):
                await fn(ctx=VALID_CTX)

    @autotests.num("208")
    @autotests.external_id("b2c3d4e5-6666-4bbb-cccc-666666666666")
    @autotests.name("MCP SDK Server: list_available_actions unexpected error → MCPServerError")
    async def test_list_available_actions_unexpected_error(self):
        # Arrange
        with autotests.step("Create server with error provider"):
            server = OnlinetlabsMCPServer("test", FakeErrorAllProtocols())
            fn = _get_tool_fn(server, "list_available_actions")

        # Act & Assert
        with autotests.step("Verify unexpected error wrapped in MCPServerError"):
            with pytest.raises(MCPServerError, match="Internal server error"):
                await fn(ctx=VALID_CTX)

    @autotests.num("209")
    @autotests.external_id("b2c3d4e5-7777-4bbb-cccc-777777777777")
    @autotests.name("MCP SDK Server: execute_action unexpected error → MCPServerError")
    async def test_execute_action_unexpected_error(self):
        # Arrange
        with autotests.step("Create server with error provider"):
            server = OnlinetlabsMCPServer("test", FakeErrorAllProtocols())
            fn = _get_tool_fn(server, "execute_action")

        # Act & Assert
        with autotests.step("Verify unexpected error wrapped in MCPServerError"):
            with pytest.raises(MCPServerError, match="Internal server error"):
                await fn(ctx=VALID_CTX, action_name="restart", params={})

    # -- MCPServerError passthrough for each tool ---------------

    @autotests.num("210")
    @autotests.external_id("c3d4e5f6-1111-4ccc-dddd-111111111111")
    @autotests.name("MCP SDK Server: get_component MCPServerError passthrough")
    async def test_get_component_mcp_error_passthrough(self):
        # Arrange
        with autotests.step("Create server with custom MCPServerError impl"):
            class _Impl(FakeStateProvider):
                async def get_component(self, ctx, component_id):
                    raise MCPServerError("Custom get_component error")

            server = OnlinetlabsMCPServer("test", _Impl())
            fn = _get_tool_fn(server, "get_component")

        # Act & Assert
        with autotests.step("Verify MCPServerError passes through"):
            with pytest.raises(MCPServerError, match="Custom get_component error"):
                await fn(ctx=VALID_CTX, component_id="n1")

    @autotests.num("211")
    @autotests.external_id("c3d4e5f6-2222-4ccc-dddd-222222222222")
    @autotests.name("MCP SDK Server: get_system_overview MCPServerError passthrough")
    async def test_get_system_overview_mcp_error_passthrough(self):
        # Arrange
        with autotests.step("Create server with custom MCPServerError impl"):
            class _Impl(FakeStateProvider):
                async def get_system_overview(self, ctx):
                    raise MCPServerError("Custom overview error")

            server = OnlinetlabsMCPServer("test", _Impl())
            fn = _get_tool_fn(server, "get_system_overview")

        # Act & Assert
        with autotests.step("Verify MCPServerError passes through"):
            with pytest.raises(MCPServerError, match="Custom overview error"):
                await fn(ctx=VALID_CTX)

    @autotests.num("212")
    @autotests.external_id("c3d4e5f6-3333-4ccc-dddd-333333333333")
    @autotests.name("MCP SDK Server: list_errors MCPServerError passthrough")
    async def test_list_errors_mcp_error_passthrough(self):
        # Arrange
        with autotests.step("Create server with FakeMCPErrorAllProtocols"):
            server = OnlinetlabsMCPServer("test", FakeMCPErrorAllProtocols())
            fn = _get_tool_fn(server, "list_errors")

        # Act & Assert
        with autotests.step("Verify MCPServerError passes through"):
            with pytest.raises(MCPServerError, match="MCP error in list_errors"):
                await fn(ctx=VALID_CTX)

    @autotests.num("213")
    @autotests.external_id("c3d4e5f6-4444-4ccc-dddd-444444444444")
    @autotests.name("MCP SDK Server: get_logs MCPServerError passthrough")
    async def test_get_logs_mcp_error_passthrough(self):
        # Arrange
        with autotests.step("Create server with FakeMCPErrorAllProtocols"):
            server = OnlinetlabsMCPServer("test", FakeMCPErrorAllProtocols())
            fn = _get_tool_fn(server, "get_logs")

        # Act & Assert
        with autotests.step("Verify MCPServerError passes through"):
            with pytest.raises(MCPServerError, match="MCP error in get_logs"):
                await fn(ctx=VALID_CTX)

    @autotests.num("214")
    @autotests.external_id("c3d4e5f6-5555-4ccc-dddd-555555555555")
    @autotests.name("MCP SDK Server: list_user_actions MCPServerError passthrough")
    async def test_list_user_actions_mcp_error_passthrough(self):
        # Arrange
        with autotests.step("Create server with FakeMCPErrorAllProtocols"):
            server = OnlinetlabsMCPServer("test", FakeMCPErrorAllProtocols())
            fn = _get_tool_fn(server, "list_user_actions")

        # Act & Assert
        with autotests.step("Verify MCPServerError passes through"):
            with pytest.raises(MCPServerError, match="MCP error in list_user_actions"):
                await fn(ctx=VALID_CTX)

    @autotests.num("215")
    @autotests.external_id("c3d4e5f6-6666-4ccc-dddd-666666666666")
    @autotests.name("MCP SDK Server: list_available_actions MCPServerError passthrough")
    async def test_list_available_actions_mcp_error_passthrough(self):
        # Arrange
        with autotests.step("Create server with FakeMCPErrorAllProtocols"):
            server = OnlinetlabsMCPServer("test", FakeMCPErrorAllProtocols())
            fn = _get_tool_fn(server, "list_available_actions")

        # Act & Assert
        with autotests.step("Verify MCPServerError passes through"):
            with pytest.raises(MCPServerError, match="MCP error in list_available_actions"):
                await fn(ctx=VALID_CTX)

    @autotests.num("216")
    @autotests.external_id("c3d4e5f6-7777-4ccc-dddd-777777777777")
    @autotests.name("MCP SDK Server: execute_action MCPServerError passthrough")
    async def test_execute_action_mcp_error_passthrough(self):
        # Arrange
        with autotests.step("Create server with FakeMCPErrorAllProtocols"):
            server = OnlinetlabsMCPServer("test", FakeMCPErrorAllProtocols())
            fn = _get_tool_fn(server, "execute_action")

        # Act & Assert
        with autotests.step("Verify MCPServerError passes through"):
            with pytest.raises(MCPServerError, match="MCP error in execute_action"):
                await fn(ctx=VALID_CTX, action_name="restart", params={})
