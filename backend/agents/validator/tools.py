"""Инструменты ValidatorAgent для проверки выполнения задач."""

from mcp_sdk.context import SessionContext
from mcp_sdk.models import Component

from agents.validator.models import CheckResult


class ValidatorTools:
    """Обёртка над MCP-клиентом для валидации состояния."""

    def __init__(self, mcp_client):
        self._mcp = mcp_client

    def _build_ctx(self, input_data) -> SessionContext:
        return SessionContext(
            user_id=input_data.user_id,
            session_id=input_data.session_id,
            environment_url=input_data.environment_url,
            project_id=input_data.project_id,
        )

    async def get_current_state(self, input_data) -> list[Component]:
        """Получить текущее состояние компонентов."""
        ctx = self._build_ctx(input_data)
        return await self._mcp.list_components(ctx)

    async def check_component_status(
        self, input_data, component_id: str, expected_status: str
    ) -> CheckResult:
        """Проверить статус компонента."""
        ctx = self._build_ctx(input_data)
        component = await self._mcp.get_component(ctx, component_id)
        passed = component.status == expected_status
        return CheckResult(
            passed=passed,
            check_name=f"status:{component_id}",
            expected=expected_status,
            actual=component.status,
        )

    async def check_connectivity(
        self, input_data, source_id: str, target_id: str
    ) -> CheckResult:
        """Проверить связность между двумя компонентами."""
        ctx = self._build_ctx(input_data)
        source = await self._mcp.get_component(ctx, source_id)
        connected = target_id in source.relationships
        return CheckResult(
            passed=connected,
            check_name=f"connectivity:{source_id}->{target_id}",
            expected=f"connected to {target_id}",
            actual="connected" if connected else "not connected",
        )
