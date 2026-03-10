import pytest

from config.config_model import (
    AgentsConfig,
    ApiConfig,
    ConfigModel,
    DatabaseConfig,
    LogConfig,
    LlmProvider,
    RedisConfig,
)
from mcp_sdk.context import SessionContext
from mcp_sdk.models import (
    ActionResult,
    Component,
    ComponentDetail,
    SystemOverview,
)
from mcp_sdk.errors import ComponentNotFoundError


# ---------------------------------------------------------------------------
# Fake MCP clients
# ---------------------------------------------------------------------------

class FakeMCPClient:
    """Implements StateProvider + ActionProvider for unit tests."""

    def __init__(
        self,
        components: list[Component] | None = None,
        overview: SystemOverview | None = None,
        action_result: ActionResult | None = None,
    ):
        self._components = components or [
            Component(id="n1", name="R1", type="router", status="running", summary="Router 1"),
        ]
        self._overview = overview or SystemOverview(
            system_name="fake-gns3",
            component_count=1,
            components_by_type={"router": 1},
            components_by_status={"running": 1},
            summary="1 router running",
        )
        self._action_result = action_result or ActionResult(success=True, message="Executed")
        self.calls: list[tuple[str, tuple, dict]] = []

    async def list_components(self, ctx: SessionContext) -> list[Component]:
        self.calls.append(("list_components", (ctx,), {}))
        return self._components

    async def get_component(self, ctx: SessionContext, component_id: str) -> ComponentDetail:
        self.calls.append(("get_component", (ctx, component_id), {}))
        for c in self._components:
            if c.id == component_id:
                return ComponentDetail(
                    id=c.id, name=c.name, type=c.type, status=c.status,
                    summary=c.summary, properties={}, relationships=[],
                )
        raise ComponentNotFoundError(component_id)

    async def get_system_overview(self, ctx: SessionContext) -> SystemOverview:
        self.calls.append(("get_system_overview", (ctx,), {}))
        return self._overview

    async def execute_action(self, ctx: SessionContext, action_name: str, params: dict) -> ActionResult:
        self.calls.append(("execute_action", (ctx, action_name, params), {}))
        return ActionResult(
            success=self._action_result.success,
            message=f"Executed {action_name}",
            output=self._action_result.output,
        )


class FakeFailingMCPClient(FakeMCPClient):
    """execute_action always returns success=False."""

    async def execute_action(self, ctx, action_name, params):
        self.calls.append(("execute_action", (ctx, action_name, params), {}))
        return ActionResult(success=False, message=f"Failed: {action_name}")


# ---------------------------------------------------------------------------
# Fake StepAttempt (duck-typed object for analytics)
# ---------------------------------------------------------------------------

def make_attempt(**overrides):
    from datetime import datetime, timedelta, timezone

    now = datetime.now(tz=timezone.utc)
    defaults = {
        "id": "attempt-1",
        "step_slug": "step-1",
        "result": "pass",
        "attempt_number": 1,
        "score": 100.0,
        "started_at": now - timedelta(minutes=5),
        "ended_at": now,
        "error_details": None,
    }
    final = defaults | overrides
    return type("FakeAttempt", (), final)()


# ---------------------------------------------------------------------------
# Config fixtures
# ---------------------------------------------------------------------------

def _make_agents(**overrides):
    defaults = dict(api_key="sk-ant-test")
    return AgentsConfig(**{**defaults, **overrides})


@pytest.fixture()
def agents_config():
    return _make_agents()


@pytest.fixture()
def config_model(agents_config):
    return ConfigModel(
        database=DatabaseConfig(user="u", password="p", host="h", port=5432, db="d"),
        redis=RedisConfig(url="redis://localhost:6379/0"),
        api=ApiConfig(environment="test", jwt_secret="test-secret"),
        log=LogConfig(log_level="DEBUG"),
        agents=agents_config,
    )


# ---------------------------------------------------------------------------
# MCP fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_mcp():
    return FakeMCPClient()


@pytest.fixture()
def fake_failing_mcp():
    return FakeFailingMCPClient()
