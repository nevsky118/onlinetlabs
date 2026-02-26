"""Fake protocol implementations for testing."""

from datetime import datetime, timezone

from onlinetlabs_mcp_sdk.context import SessionContext
from onlinetlabs_mcp_sdk.errors import ComponentNotFoundError
from onlinetlabs_mcp_sdk.models import (
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


class FakeStateProvider:
    async def list_components(self, ctx: SessionContext) -> list[Component]:
        return [
            Component(id="n1", name="R1", type="router", status="running", summary="Router 1")
        ]

    async def get_component(self, ctx: SessionContext, component_id: str) -> ComponentDetail:
        if component_id == "nonexistent":
            raise ComponentNotFoundError(component_id=component_id)
        return ComponentDetail(
            id=component_id, name="R1", type="router", status="running",
            summary="Router 1", properties={"cpu": 1}, relationships=[],
        )

    async def get_system_overview(self, ctx: SessionContext) -> SystemOverview:
        return SystemOverview(
            system_name="fake", component_count=1,
            components_by_type={"router": 1}, components_by_status={"running": 1},
            summary="1 router",
        )


class FakeLogProvider(FakeStateProvider):
    async def list_errors(self, ctx, since=None):
        return [ErrorEntry(timestamp=datetime.now(tz=timezone.utc), level=LogLevel.ERROR, message="Link down")]

    async def get_logs(self, ctx, level=LogLevel.ALL, limit=100):
        return [LogEntry(timestamp=datetime.now(tz=timezone.utc), level=LogLevel.INFO, source="system", message="Started")]


class FakeHistoryProvider(FakeStateProvider):
    async def list_user_actions(self, ctx, limit=50):
        return [UserAction(timestamp=datetime.now(tz=timezone.utc), action="configure", success=True)]


class FakeActionProvider(FakeStateProvider):
    async def list_available_actions(self, ctx, component_id=None):
        return [ActionSpec(name="restart_node", description="Restart a node", parameters={"type": "object", "properties": {"node_id": {"type": "string"}}}, component_types=["router"])]

    async def execute_action(self, ctx, action_name, params):
        return ActionResult(success=True, message=f"Executed {action_name}")


class FakeAllProtocols(FakeStateProvider):
    """Implements all 4 protocols."""

    async def list_errors(self, ctx, since=None):
        return [ErrorEntry(timestamp=datetime.now(tz=timezone.utc), level=LogLevel.ERROR, message="Link down")]

    async def get_logs(self, ctx, level=LogLevel.ALL, limit=100):
        return [LogEntry(timestamp=datetime.now(tz=timezone.utc), level=LogLevel.INFO, source="system", message="Started")]

    async def list_user_actions(self, ctx, limit=50):
        return [UserAction(timestamp=datetime.now(tz=timezone.utc), action="configure", success=True)]

    async def list_available_actions(self, ctx, component_id=None):
        return [ActionSpec(name="restart_node", description="Restart a node", parameters={"type": "object", "properties": {}}, component_types=["router"])]

    async def execute_action(self, ctx, action_name, params):
        return ActionResult(success=True, message=f"Executed {action_name}")


class FakeErrorStateProvider:
    """StateProvider that raises on every call — for error handling tests."""

    async def list_components(self, ctx):
        raise RuntimeError("Unexpected failure")

    async def get_component(self, ctx, component_id):
        raise RuntimeError("Unexpected failure")

    async def get_system_overview(self, ctx):
        raise RuntimeError("Unexpected failure")


class FakeErrorAllProtocols(FakeErrorStateProvider):
    """All protocols, every method raises RuntimeError."""

    async def list_errors(self, ctx, since=None):
        raise RuntimeError("Unexpected failure")

    async def get_logs(self, ctx, level=None, limit=100):
        raise RuntimeError("Unexpected failure")

    async def list_user_actions(self, ctx, limit=50):
        raise RuntimeError("Unexpected failure")

    async def list_available_actions(self, ctx, component_id=None):
        raise RuntimeError("Unexpected failure")

    async def execute_action(self, ctx, action_name, params):
        raise RuntimeError("Unexpected failure")


class MCPErrorProvider:
    """StateProvider where every method raises MCPServerError — for passthrough tests."""

    async def list_components(self, ctx):
        from onlinetlabs_mcp_sdk.errors import MCPServerError
        raise MCPServerError("Custom MCP error")

    async def get_component(self, ctx, component_id):
        from onlinetlabs_mcp_sdk.errors import MCPServerError
        raise MCPServerError("Custom MCP error")

    async def get_system_overview(self, ctx):
        from onlinetlabs_mcp_sdk.errors import MCPServerError
        raise MCPServerError("Custom MCP error")


class FakeMCPErrorAllProtocols(FakeStateProvider):
    """All protocols, every non-state method raises MCPServerError."""

    async def list_errors(self, ctx, since=None):
        from onlinetlabs_mcp_sdk.errors import MCPServerError
        raise MCPServerError("MCP error in list_errors")

    async def get_logs(self, ctx, level=None, limit=100):
        from onlinetlabs_mcp_sdk.errors import MCPServerError
        raise MCPServerError("MCP error in get_logs")

    async def list_user_actions(self, ctx, limit=50):
        from onlinetlabs_mcp_sdk.errors import MCPServerError
        raise MCPServerError("MCP error in list_user_actions")

    async def list_available_actions(self, ctx, component_id=None):
        from onlinetlabs_mcp_sdk.errors import MCPServerError
        raise MCPServerError("MCP error in list_available_actions")

    async def execute_action(self, ctx, action_name, params):
        from onlinetlabs_mcp_sdk.errors import MCPServerError
        raise MCPServerError("MCP error in execute_action")
