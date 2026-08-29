"""Test data for the MCP server seam: stand-ins for the server and its transport."""

from mcp_sdk.models import ActionResult, ComponentDetail, LogLevel, SystemOverview


class StubServerData:
    """Stand-in for OnlinetlabsMCPServer that captures the registered tool functions."""

    def __init__(self):
        self.tools: dict = {}
        self.descriptions: dict = {}

    def domain_tool(self, **kwargs):
        """Registers the decorated function instead of exposing it over MCP."""
        description = kwargs.get("description", "")

        def wrapper(fn):
            self.tools[fn.__name__] = fn
            self.descriptions[fn.__name__] = description
            return fn

        return wrapper


class FakeMcpTransportData:
    """FastMCP stand-in: captures registered tools by name, with no real transport."""

    def __init__(self, name=None, **kwargs):
        self.name = name
        self.tools: dict = {}

    def tool(self, **kwargs):
        """Registers the decorated function instead of publishing it."""

        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return decorator


class ProbeImplData:
    """Implements all four SDK protocols, optionally raising from every method."""

    def __init__(self, raise_error: Exception | None = None):
        self.raise_error = raise_error

    def _maybe_raise(self) -> None:
        """Raises the prepared error, if one was given."""
        if self.raise_error is not None:
            raise self.raise_error

    async def list_components(self, ctx):
        """No components."""
        self._maybe_raise()
        return []

    async def get_component(self, ctx, component_id):
        """A minimal component detail."""
        self._maybe_raise()
        return ComponentDetail(
            id=component_id,
            name="n",
            type="t",
            status="s",
            summary="sum",
            properties={},
            relationships=[],
        )

    async def get_system_overview(self, ctx):
        """An empty system."""
        self._maybe_raise()
        return SystemOverview(
            system_name="x",
            component_count=0,
            components_by_type={},
            components_by_status={},
            summary="s",
        )

    async def list_errors(self, ctx, since=None):
        """No errors."""
        self._maybe_raise()
        return []

    async def get_logs(self, ctx, level=LogLevel.ALL, limit=100):
        """No logs."""
        self._maybe_raise()
        return []

    async def list_user_actions(self, ctx, limit=50):
        """No actions."""
        self._maybe_raise()
        return []

    async def list_available_actions(self, ctx, component_id=None):
        """No available actions."""
        self._maybe_raise()
        return []

    async def execute_action(self, ctx, action_name, params):
        """A successful no-op."""
        self._maybe_raise()
        return ActionResult(success=True, message="ok")
