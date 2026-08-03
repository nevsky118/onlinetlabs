"""Tests for the `_tool_errors` error decorator in mcp_sdk.server.OnlinetlabsMCPServer.

They check the error contract of the tool functions. An invalid SessionContext →
SessionContextError, a domain MCPServerError propagates unchanged, and an
unexpected exception is masked as "Internal server error". Plus two bonus fixes,
a bad level/since is no longer masked and surfaces as SessionContextError.
"""

import pytest
from mcp_sdk.errors import ComponentNotFoundError, MCPServerError, SessionContextError
from mcp_sdk.models import ActionResult, ComponentDetail, LogLevel, SystemOverview
from mcp_sdk.server import OnlinetlabsMCPServer
from mcp_sdk.testing import autotest

pytestmark = [pytest.mark.unit]

GNS3_URL = "http://gns3-test:3080"

ALL_TOOL_NAMES = [
    "list_components",
    "get_component",
    "get_system_overview",
    "list_errors",
    "get_logs",
    "list_user_actions",
    "list_available_actions",
    "execute_action",
]


def _ctx_dict(**overrides) -> dict:
    defaults = dict(user_id="u1", session_id="s1", environment_url=GNS3_URL, project_id="proj-1")
    return defaults | overrides


def _call_kwargs(name: str, ctx: dict) -> dict:
    """Keyword arguments sufficient to call each of the 8 tool functions."""
    if name == "get_component":
        return {"ctx": ctx, "component_id": "c1"}
    if name == "execute_action":
        return {"ctx": ctx, "action_name": "start_all_nodes", "params": {}}
    return {"ctx": ctx}


class _ProbeImpl:
    """Implementation of all 4 SDK protocols with a controllable exception from the impl methods."""

    def __init__(self, raise_error: Exception | None = None) -> None:
        self._raise_error = raise_error

    def _maybe_raise(self) -> None:
        if self._raise_error is not None:
            raise self._raise_error

    async def list_components(self, ctx):
        self._maybe_raise()
        return []

    async def get_component(self, ctx, component_id):
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
        self._maybe_raise()
        return SystemOverview(
            system_name="x",
            component_count=0,
            components_by_type={},
            components_by_status={},
            summary="s",
        )

    async def list_errors(self, ctx, since=None):
        self._maybe_raise()
        return []

    async def get_logs(self, ctx, level=LogLevel.ALL, limit=100):
        self._maybe_raise()
        return []

    async def list_user_actions(self, ctx, limit=50):
        self._maybe_raise()
        return []

    async def list_available_actions(self, ctx, component_id=None):
        self._maybe_raise()
        return []

    async def execute_action(self, ctx, action_name, params):
        self._maybe_raise()
        return ActionResult(success=True, message="ok")


class _FakeMCP:
    """FastMCP stand-in, captures the registered tool functions by name with no real transport."""

    def __init__(self, name, **kwargs) -> None:
        self.tools: dict[str, callable] = {}

    def tool(self, **kwargs):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return decorator


@pytest.fixture()
def make_server(monkeypatch):
    """Builds an OnlinetlabsMCPServer on top of _FakeMCP, returning a factory keyed by raise_error."""
    monkeypatch.setattr("mcp_sdk.server.FastMCP", _FakeMCP)

    def _make(raise_error: Exception | None = None) -> OnlinetlabsMCPServer:
        return OnlinetlabsMCPServer(
            name="probe", implementation=_ProbeImpl(raise_error=raise_error)
        )

    return _make


class TestToolErrorContract:
    @autotest.num("827")
    @autotest.external_id("356217db-a3bf-4373-b8af-d4b0a9a240ae")
    @autotest.name("_tool_errors: invalid ctx → SessionContextError for all 8 tools")
    async def test_356217db_invalid_ctx_raises_session_context_error(self, make_server):
        with autotest.step("Set up a server with the full set of protocols"):
            server = make_server()

        with autotest.step("For each tool, call with a ctx missing required fields"):
            for name in ALL_TOOL_NAMES:
                fn = server.mcp.tools[name]
                kwargs = _call_kwargs(name, {"user_id": "u1"})
                with pytest.raises(SessionContextError):
                    await fn(**kwargs)

    @autotest.num("828")
    @autotest.external_id("760061cd-e6e3-485c-8cc5-c1789c17be3d")
    @autotest.name("_tool_errors: a domain MCPServerError propagates unwrapped")
    async def test_760061cd_domain_error_passthrough(self, make_server):
        with autotest.step("impl raises ComponentNotFoundError"):
            server = make_server(raise_error=ComponentNotFoundError(component_id="c1"))

        with autotest.step("Call list_components"):
            fn = server.mcp.tools["list_components"]
            with pytest.raises(ComponentNotFoundError):
                await fn(ctx=_ctx_dict())

    @autotest.num("829")
    @autotest.external_id("881a7ba6-da1f-4346-9be1-389c25ffd515")
    @autotest.name("_tool_errors: unexpected exception → MCPServerError('Internal server error')")
    async def test_881a7ba6_unexpected_error_masked(self, make_server):
        with autotest.step("impl raises an arbitrary RuntimeError"):
            server = make_server(raise_error=RuntimeError("boom"))

        with autotest.step("Call list_components and assert the masking"):
            fn = server.mcp.tools["list_components"]
            with pytest.raises(MCPServerError) as exc_info:
                await fn(ctx=_ctx_dict())
            assert str(exc_info.value) == "Internal server error"


class TestBonusArgumentValidation:
    @autotest.num("830")
    @autotest.external_id("433369b4-ad0d-4c39-95bb-420c39c0b72c")
    @autotest.name("get_logs: invalid level → SessionContextError, not Internal server error")
    async def test_433369b4_get_logs_invalid_level_raises_session_context_error(self, make_server):
        with autotest.step("Set up the server"):
            server = make_server()
            fn = server.mcp.tools["get_logs"]

        with autotest.step("Call with a nonexistent level"):
            with pytest.raises(SessionContextError) as exc_info:
                await fn(ctx=_ctx_dict(), level="not-a-level")
            assert "not-a-level" in str(exc_info.value)

    @autotest.num("831")
    @autotest.external_id("a03f92dc-71cd-4332-92b1-e0678ec5f80e")
    @autotest.name("list_errors: invalid since → SessionContextError, not Internal server error")
    async def test_a03f92dc_list_errors_invalid_since_raises_session_context_error(
        self, make_server
    ):
        with autotest.step("Set up the server"):
            server = make_server()
            fn = server.mcp.tools["list_errors"]

        with autotest.step("Call with an invalid since"):
            with pytest.raises(SessionContextError) as exc_info:
                await fn(ctx=_ctx_dict(), since="not-a-date")
            assert "not-a-date" in str(exc_info.value)
