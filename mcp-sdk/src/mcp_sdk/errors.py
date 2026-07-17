"""MCP server exception hierarchy."""


class MCPServerError(Exception):
    """Base MCP server error."""


class TargetSystemConnectionError(MCPServerError):
    """Failed to connect to the target system."""


class TargetSystemAPIError(MCPServerError):
    """The target system returned an error."""

    def __init__(
        self,
        status_code: int,
        response_body: str | None = None,
        message: str | None = None,
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message or f"Target system API error: {status_code}")


class ComponentNotFoundError(MCPServerError):
    """Component not found in the target system."""

    def __init__(self, component_id: str, message: str | None = None):
        self.component_id = component_id
        super().__init__(message or f"Component not found: {component_id}")


class ActionExecutionError(MCPServerError):
    """Error executing an action in the target system."""

    def __init__(self, action_name: str, reason: str):
        self.action_name = action_name
        self.reason = reason
        super().__init__(f"Action '{action_name}' failed: {reason}")


class SessionContextError(MCPServerError):
    """Invalid or missing session context."""
