"""Conformance test suite для проверки соответствия MCP-сервера стандарту."""

import pytest

from mcp_sdk.errors import ComponentNotFoundError
from mcp_sdk.models import (
    ActionResult,
    ActionSpec,
    Component,
    ComponentDetail,
    ErrorEntry,
    LogEntry,
    SystemOverview,
    UserAction,
)
from mcp_sdk.protocols import (
    ActionProvider,
    HistoryProvider,
    LogProvider,
    StateProvider,
)
from mcp_sdk.testing import reports as autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_greater_equal,
    assert_is_instance,
    assert_is_not_none,
    assert_true,
)


class ConformanceTestSuite:
    """Базовый набор тестов соответствия стандарту.

    Разработчик наследует этот класс и предоставляет фикстуры
    server_impl и mock_session_ctx.
    """

    # StateProvider

    @autotest.num("500")
    @autotest.external_id("c1a2b3d4-e5f6-7890-abcd-100000000001")
    @autotest.name("Conformance: list_components возвращает list[Component]")
    async def test_c1a2b3d4_list_components_returns_list(self, server_impl, mock_session_ctx):
        """list_components возвращает list[Component]."""
        if not isinstance(server_impl, StateProvider):
            pytest.skip("StateProvider not implemented")

        # Act
        with autotest.step("Вызываем list_components"):
            result = await server_impl.list_components(mock_session_ctx)

        # Assert
        with autotest.step("Проверяем, что результат — список"):
            assert_is_instance(result, list, "list_components должен вернуть list")

        with autotest.step("Проверяем, что каждый элемент — Component"):
            for item in result:
                assert_is_instance(item, Component, f"Элемент {item} не является Component")

    @autotest.num("501")
    @autotest.external_id("d2b3c4e5-f6a7-8901-bcde-200000000002")
    @autotest.name("Conformance: get_component возвращает ComponentDetail")
    async def test_d2b3c4e5_get_component_returns_detail(self, server_impl, mock_session_ctx):
        """get_component возвращает ComponentDetail с корректным id."""
        if not isinstance(server_impl, StateProvider):
            pytest.skip("StateProvider not implemented")

        # Arrange
        with autotest.step("Получаем список компонентов"):
            components = await server_impl.list_components(mock_session_ctx)

        if not components:
            pytest.skip("No components to test")

        # Act
        with autotest.step(f"Запрашиваем компонент по id={components[0].id}"):
            result = await server_impl.get_component(mock_session_ctx, components[0].id)

        # Assert
        with autotest.step("Проверяем тип и id"):
            assert_is_instance(result, ComponentDetail, "get_component должен вернуть ComponentDetail")
            assert_equal(result.id, components[0].id, f"id не совпадает: {result.id} != {components[0].id}")

    @autotest.num("502")
    @autotest.external_id("e3c4d5f6-a7b8-9012-cdef-300000000003")
    @autotest.name("Conformance: get_component с несуществующим ID — ComponentNotFoundError")
    async def test_e3c4d5f6_get_component_not_found_raises(self, server_impl, mock_session_ctx):
        """get_component с несуществующим ID вызывает ComponentNotFoundError."""
        if not isinstance(server_impl, StateProvider):
            pytest.skip("StateProvider not implemented")

        # Act + Assert
        with autotest.step("Запрашиваем компонент с несуществующим ID"):
            with pytest.raises(ComponentNotFoundError):
                await server_impl.get_component(mock_session_ctx, "nonexistent")

    @autotest.num("503")
    @autotest.external_id("f4d5e6a7-b8c9-0123-defa-400000000004")
    @autotest.name("Conformance: get_system_overview возвращает SystemOverview")
    async def test_f4d5e6a7_get_system_overview_returns_overview(self, server_impl, mock_session_ctx):
        """get_system_overview возвращает SystemOverview."""
        if not isinstance(server_impl, StateProvider):
            pytest.skip("StateProvider not implemented")

        # Act
        with autotest.step("Вызываем get_system_overview"):
            result = await server_impl.get_system_overview(mock_session_ctx)

        # Assert
        with autotest.step("Проверяем тип и обязательные поля"):
            assert_is_instance(result, SystemOverview, "get_system_overview должен вернуть SystemOverview")
            assert_is_not_none(result.system_name, "system_name не должен быть None")
            assert_greater_equal(result.component_count, 0, "component_count должен быть >= 0")

    # LogProvider

    @autotest.num("504")
    @autotest.external_id("a5e6f7b8-c9d0-1234-efab-500000000005")
    @autotest.name("Conformance: list_errors возвращает list[ErrorEntry]")
    async def test_a5e6f7b8_list_errors_returns_list(self, server_impl, mock_session_ctx):
        """list_errors возвращает list[ErrorEntry]."""
        if not isinstance(server_impl, LogProvider):
            pytest.skip("LogProvider not implemented")

        # Act
        with autotest.step("Вызываем list_errors"):
            result = await server_impl.list_errors(mock_session_ctx)

        # Assert
        with autotest.step("Проверяем, что результат — список ErrorEntry"):
            assert_is_instance(result, list, "list_errors должен вернуть list")
            for item in result:
                assert_is_instance(item, ErrorEntry, f"Элемент {item} не является ErrorEntry")

    @autotest.num("505")
    @autotest.external_id("b6f7a8c9-d0e1-2345-fabc-600000000006")
    @autotest.name("Conformance: get_logs возвращает list[LogEntry]")
    async def test_b6f7a8c9_get_logs_returns_list(self, server_impl, mock_session_ctx):
        """get_logs возвращает list[LogEntry]."""
        if not isinstance(server_impl, LogProvider):
            pytest.skip("LogProvider not implemented")

        # Act
        with autotest.step("Вызываем get_logs"):
            result = await server_impl.get_logs(mock_session_ctx)

        # Assert
        with autotest.step("Проверяем, что результат — список LogEntry"):
            assert_is_instance(result, list, "get_logs должен вернуть list")
            for item in result:
                assert_is_instance(item, LogEntry, f"Элемент {item} не является LogEntry")

    # HistoryProvider

    @autotest.num("506")
    @autotest.external_id("c7a8b9d0-e1f2-3456-abcd-700000000007")
    @autotest.name("Conformance: list_user_actions возвращает list[UserAction]")
    async def test_c7a8b9d0_list_user_actions_returns_list(self, server_impl, mock_session_ctx):
        """list_user_actions возвращает list[UserAction]."""
        if not isinstance(server_impl, HistoryProvider):
            pytest.skip("HistoryProvider not implemented")

        # Act
        with autotest.step("Вызываем list_user_actions"):
            result = await server_impl.list_user_actions(mock_session_ctx)

        # Assert
        with autotest.step("Проверяем, что результат — список UserAction"):
            assert_is_instance(result, list, "list_user_actions должен вернуть list")
            for item in result:
                assert_is_instance(item, UserAction, f"Элемент {item} не является UserAction")

    # ActionProvider

    @autotest.num("507")
    @autotest.external_id("d8b9c0e1-f2a3-4567-bcde-800000000008")
    @autotest.name("Conformance: list_available_actions возвращает list[ActionSpec]")
    async def test_d8b9c0e1_list_available_actions_returns_list(self, server_impl, mock_session_ctx):
        """list_available_actions возвращает list[ActionSpec]."""
        if not isinstance(server_impl, ActionProvider):
            pytest.skip("ActionProvider not implemented")

        # Act
        with autotest.step("Вызываем list_available_actions"):
            result = await server_impl.list_available_actions(mock_session_ctx)

        # Assert
        with autotest.step("Проверяем, что результат — список ActionSpec"):
            assert_is_instance(result, list, "list_available_actions должен вернуть list")
            for item in result:
                assert_is_instance(item, ActionSpec, f"Элемент {item} не является ActionSpec")

    @autotest.num("508")
    @autotest.external_id("e9c0d1f2-a3b4-5678-cdef-900000000009")
    @autotest.name("Conformance: execute_action возвращает ActionResult")
    async def test_e9c0d1f2_execute_action_returns_result(self, server_impl, mock_session_ctx):
        """execute_action возвращает ActionResult."""
        if not isinstance(server_impl, ActionProvider):
            pytest.skip("ActionProvider not implemented")

        # Arrange
        with autotest.step("Получаем список доступных действий"):
            actions = await server_impl.list_available_actions(mock_session_ctx)

        if not actions:
            pytest.skip("No actions available to test")

        # Act
        with autotest.step(f"Выполняем действие {actions[0].name}"):
            result = await server_impl.execute_action(
                mock_session_ctx,
                action_name=actions[0].name,
                params={},
            )

        # Assert
        with autotest.step("Проверяем, что результат — ActionResult"):
            assert_is_instance(result, ActionResult, "execute_action должен вернуть ActionResult")
