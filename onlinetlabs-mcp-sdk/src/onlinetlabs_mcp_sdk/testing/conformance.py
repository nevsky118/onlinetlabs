"""Conformance test suite для проверки соответствия MCP-сервера стандарту."""

import pytest

from onlinetlabs_mcp_sdk.errors import ComponentNotFoundError
from onlinetlabs_mcp_sdk.models import (
    ActionResult,
    ActionSpec,
    Component,
    ComponentDetail,
    ErrorEntry,
    LogEntry,
    SystemOverview,
    UserAction,
)
from onlinetlabs_mcp_sdk.protocols import (
    ActionProvider,
    HistoryProvider,
    LogProvider,
    StateProvider,
)


class ConformanceTestSuite:
    """Базовый набор тестов соответствия стандарту.

    Разработчик наследует этот класс и предоставляет фикстуры
    server_impl и mock_session_ctx.
    """

    async def test_list_components_returns_list(self, server_impl, mock_session_ctx):
        """list_components возвращает list[Component]."""
        if not isinstance(server_impl, StateProvider):
            pytest.skip("StateProvider not implemented")
        result = await server_impl.list_components(mock_session_ctx)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, Component)

    async def test_get_component_returns_detail(self, server_impl, mock_session_ctx):
        """get_component возвращает ComponentDetail."""
        if not isinstance(server_impl, StateProvider):
            pytest.skip("StateProvider not implemented")
        components = await server_impl.list_components(mock_session_ctx)
        if not components:
            pytest.skip("No components to test")
        result = await server_impl.get_component(mock_session_ctx, components[0].id)
        assert isinstance(result, ComponentDetail)
        assert result.id == components[0].id

    async def test_get_component_not_found_raises(self, server_impl, mock_session_ctx):
        """get_component с несуществующим ID вызывает ComponentNotFoundError."""
        if not isinstance(server_impl, StateProvider):
            pytest.skip("StateProvider not implemented")
        with pytest.raises(ComponentNotFoundError):
            await server_impl.get_component(mock_session_ctx, "nonexistent")

    async def test_get_system_overview_returns_overview(
        self, server_impl, mock_session_ctx
    ):
        """get_system_overview возвращает SystemOverview."""
        if not isinstance(server_impl, StateProvider):
            pytest.skip("StateProvider not implemented")
        result = await server_impl.get_system_overview(mock_session_ctx)
        assert isinstance(result, SystemOverview)
        assert result.system_name
        assert result.component_count >= 0

    async def test_list_errors_returns_list(self, server_impl, mock_session_ctx):
        """list_errors возвращает list[ErrorEntry]."""
        if not isinstance(server_impl, LogProvider):
            pytest.skip("LogProvider not implemented")
        result = await server_impl.list_errors(mock_session_ctx)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, ErrorEntry)

    async def test_get_logs_returns_list(self, server_impl, mock_session_ctx):
        """get_logs возвращает list[LogEntry]."""
        if not isinstance(server_impl, LogProvider):
            pytest.skip("LogProvider not implemented")
        result = await server_impl.get_logs(mock_session_ctx)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, LogEntry)

    async def test_list_user_actions_returns_list(self, server_impl, mock_session_ctx):
        """list_user_actions возвращает list[UserAction]."""
        if not isinstance(server_impl, HistoryProvider):
            pytest.skip("HistoryProvider not implemented")
        result = await server_impl.list_user_actions(mock_session_ctx)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, UserAction)

    async def test_list_available_actions_returns_list(
        self, server_impl, mock_session_ctx
    ):
        """list_available_actions возвращает list[ActionSpec]."""
        if not isinstance(server_impl, ActionProvider):
            pytest.skip("ActionProvider not implemented")
        result = await server_impl.list_available_actions(mock_session_ctx)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, ActionSpec)

    async def test_execute_action_returns_result(self, server_impl, mock_session_ctx):
        """execute_action возвращает ActionResult."""
        if not isinstance(server_impl, ActionProvider):
            pytest.skip("ActionProvider not implemented")
        actions = await server_impl.list_available_actions(mock_session_ctx)
        if not actions:
            pytest.skip("No actions available to test")
        result = await server_impl.execute_action(
            mock_session_ctx,
            action_name=actions[0].name,
            params={},
        )
        assert isinstance(result, ActionResult)
