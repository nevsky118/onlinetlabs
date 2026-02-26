"""Data builders with sensible defaults."""

from datetime import datetime, timezone
from typing import Any

from onlinetlabs_mcp_sdk.context import ServerCapabilities, SessionContext
from onlinetlabs_mcp_sdk.models import (
    ActionResult, ActionSpec, Component, ComponentDetail,
    ErrorEntry, LogEntry, LogLevel, SystemOverview, UserAction,
)


def build_component(**overrides: Any) -> Component:
    defaults = {"id": "node-1", "name": "Router1", "type": "router", "status": "running", "summary": "Core router"}
    return Component(**(defaults | overrides))


def build_component_detail(**overrides: Any) -> ComponentDetail:
    defaults = {"id": "node-1", "name": "Router1", "type": "router", "status": "running", "summary": "Core router", "properties": {"cpu": 2}, "relationships": []}
    return ComponentDetail(**(defaults | overrides))


def build_system_overview(**overrides: Any) -> SystemOverview:
    defaults = {"system_name": "TestSystem", "component_count": 1, "components_by_type": {"router": 1}, "components_by_status": {"running": 1}, "summary": "1 device"}
    return SystemOverview(**(defaults | overrides))


def build_log_entry(**overrides: Any) -> LogEntry:
    defaults = {"timestamp": datetime.now(tz=timezone.utc), "level": LogLevel.INFO, "source": "system", "message": "Log message"}
    return LogEntry(**(defaults | overrides))


def build_error_entry(**overrides: Any) -> ErrorEntry:
    defaults = {"timestamp": datetime.now(tz=timezone.utc), "level": LogLevel.ERROR, "message": "Error occurred"}
    return ErrorEntry(**(defaults | overrides))


def build_user_action(**overrides: Any) -> UserAction:
    defaults = {"timestamp": datetime.now(tz=timezone.utc), "action": "configure", "success": True}
    return UserAction(**(defaults | overrides))


def build_action_spec(**overrides: Any) -> ActionSpec:
    defaults = {"name": "restart_node", "description": "Restart a node", "parameters": {"type": "object", "properties": {}}, "component_types": ["router"]}
    return ActionSpec(**(defaults | overrides))


def build_action_result(**overrides: Any) -> ActionResult:
    defaults = {"success": True, "message": "Done"}
    return ActionResult(**(defaults | overrides))


def build_session_context(**overrides: Any) -> SessionContext:
    defaults = {"user_id": "test-user", "session_id": "test-session", "environment_url": "http://localhost:3080"}
    return SessionContext(**(defaults | overrides))


def build_server_capabilities(**overrides: Any) -> ServerCapabilities:
    defaults = {"system_name": "TestSystem", "capabilities": ["state"]}
    return ServerCapabilities(**(defaults | overrides))
