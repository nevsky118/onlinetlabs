import pytest

from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.protocols]


class TestStateProvider:
    @autotests.num("140")
    @autotests.external_id("ff0d1edd-5e0f-4085-805d-3e2649ae2028")
    @autotests.name("MCP SDK Protocols: класс с методами — isinstance StateProvider")
    def test_implements_state_provider(self):
        """Класс с нужными методами — isinstance StateProvider."""

        # Arrange
        from onlinetlabs_mcp_sdk.context import SessionContext
        from onlinetlabs_mcp_sdk.models import (
            Component,
            ComponentDetail,
            SystemOverview,
        )
        from onlinetlabs_mcp_sdk.protocols import StateProvider

        class FakeState:
            async def list_components(self, ctx: SessionContext) -> list[Component]:
                return []

            async def get_component(
                self, ctx: SessionContext, component_id: str
            ) -> ComponentDetail:
                return ComponentDetail(
                    id=component_id,
                    name="x",
                    type="x",
                    status="x",
                    summary="x",
                    properties={},
                    relationships=[],
                )

            async def get_system_overview(self, ctx: SessionContext) -> SystemOverview:
                return SystemOverview(
                    system_name="test",
                    component_count=0,
                    components_by_type={},
                    components_by_status={},
                    summary="empty",
                )

        # Act & Assert
        with autotests.step("Проверяем isinstance"):
            assert isinstance(FakeState(), StateProvider)

    @autotests.num("141")
    @autotests.external_id("3d499da1-ac86-495e-91aa-bc947e32c2a3")
    @autotests.name("MCP SDK Protocols: неполный класс — не StateProvider")
    def test_incomplete_not_provider(self):
        """Класс без всех методов — не StateProvider."""

        # Arrange
        from onlinetlabs_mcp_sdk.protocols import StateProvider

        class Incomplete:
            async def list_components(self, ctx):
                return []

        # Act & Assert
        with autotests.step("Проверяем что Incomplete не StateProvider"):
            assert not isinstance(Incomplete(), StateProvider)


class TestLogProvider:
    @autotests.num("142")
    @autotests.external_id("7af76189-6ab2-49de-a420-fbcc81e4ffad")
    @autotests.name("MCP SDK Protocols: класс с методами — isinstance LogProvider")
    def test_implements_log_provider(self):
        """Проверяет реализацию LogProvider."""

        # Arrange
        from onlinetlabs_mcp_sdk.protocols import LogProvider

        class FakeLogs:
            async def list_errors(self, ctx, since=None):
                return []

            async def get_logs(self, ctx, level=None, limit=100):
                return []

        # Act & Assert
        with autotests.step("Проверяем isinstance"):
            assert isinstance(FakeLogs(), LogProvider)


class TestHistoryProvider:
    @autotests.num("143")
    @autotests.external_id("67e5767b-53bf-4e08-a0bd-272ef4cbcda1")
    @autotests.name("MCP SDK Protocols: класс с методами — isinstance HistoryProvider")
    def test_implements_history_provider(self):
        """Проверяет реализацию HistoryProvider."""

        # Arrange
        from onlinetlabs_mcp_sdk.protocols import HistoryProvider

        class FakeHistory:
            async def list_user_actions(self, ctx, limit=50):
                return []

        # Act & Assert
        with autotests.step("Проверяем isinstance"):
            assert isinstance(FakeHistory(), HistoryProvider)


class TestActionProvider:
    @autotests.num("144")
    @autotests.external_id("c9031cb9-1ce7-4b02-ae0b-f9e671a63702")
    @autotests.name("MCP SDK Protocols: класс с методами — isinstance ActionProvider")
    def test_implements_action_provider(self):
        """Проверяет реализацию ActionProvider."""

        # Arrange
        from onlinetlabs_mcp_sdk.protocols import ActionProvider

        class FakeActions:
            async def list_available_actions(self, ctx, component_id=None):
                return []

            async def execute_action(self, ctx, action_name="", params=None):
                return None

        # Act & Assert
        with autotests.step("Проверяем isinstance"):
            assert isinstance(FakeActions(), ActionProvider)
