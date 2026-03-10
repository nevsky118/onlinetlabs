"""Инструменты LabAgent для работы с лаб-средой."""

from mcp_sdk.context import SessionContext
from mcp_sdk.models import ActionResult, Component, ComponentDetail


class LabTools:
    """Обёртка над MCP-клиентом для операций с лаб-средой."""

    def __init__(self, mcp_client):
        self._mcp = mcp_client

    def _build_ctx(self, input_data) -> SessionContext:
        """Построить SessionContext из input модели."""
        return SessionContext(
            user_id=input_data.user_id,
            session_id=input_data.session_id,
            environment_url=input_data.environment_url,
            project_id=input_data.project_id,
        )

    async def get_topology(self, input_data) -> list[Component]:
        """Получить список компонентов лаб-среды."""
        ctx = self._build_ctx(input_data)
        return await self._mcp.list_components(ctx)

    async def get_component_state(
        self, input_data, component_id: str
    ) -> ComponentDetail:
        """Получить детальное состояние компонента."""
        ctx = self._build_ctx(input_data)
        return await self._mcp.get_component(ctx, component_id)

    async def execute_action(
        self, input_data, action_name: str, params: dict
    ) -> ActionResult:
        """Выполнить действие через MCP ActionProvider."""
        ctx = self._build_ctx(input_data)
        return await self._mcp.execute_action(ctx, action_name, params)

    async def interpret_state(
        self, input_data, components: list[Component]
    ) -> str:
        """Интерпретация списка компонентов в текстовое описание."""
        lines = []
        for c in components:
            lines.append(f"{c.name} ({c.type}): {c.status}")
        return "Состояние среды:\n" + "\n".join(lines)
