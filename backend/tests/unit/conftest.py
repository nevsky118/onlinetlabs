# Shared conftest for unit tests.

import os

# Override required env vars before importing modules that need them
# at load time (config.env_config_loader is triggered lazily from db.session, etc.).
_TEST_ENV_DEFAULTS = {
    "DB_USER": "test",
    "DB_PASSWORD": "test",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "test",
    "REDIS_URL": "redis://localhost:6379/0",
    "ENVIRONMENT": "test",
    "JWT_SECRET": "test-jwt-secret",
    "LOG_LEVEL": "DEBUG",
    "CRED_ENCRYPTION_KEY": "r1juy4ePJMqjrYbqXaCw7kDPq8Gwudckyv0wiIBIwfU=",
    "INTERNAL_API_TOKEN": "test-internal-token",
    "YANDEX_API_KEY": "sk-test",
    "YANDEX_FOLDER": "test-folder",
    "AGENTS_CHAT_MODEL": "yandex-gpt-5.1",
    "AGENTS_INTERVENTION_MODEL": "yandex-gpt-5.1",
    "FRONTEND_URL": "http://localhost:3000",
    "GNS3_SERVICE_URL": "http://localhost:8101",
    "GNS3_PUBLIC_URL": "http://localhost:3080",
    "GNS3_INTERNAL_URL": "http://localhost:3080",
    "MCP_SERVER_URL": "http://localhost:8100",
}
for _key, _value in _TEST_ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)

import pytest
from mcp_sdk.context import SessionContext
from mcp_sdk.errors import ComponentNotFoundError
from mcp_sdk.models import (
    ActionResult,
    Component,
    ComponentDetail,
    SystemOverview,
)

from config.config_model import (
    AgentsConfig,
    ApiConfig,
    ConfigModel,
    DatabaseConfig,
    GNS3Config,
    LlmProvider,
    LogConfig,
    MCPConfig,
    ModelEntry,
    ProviderCreds,
    RedisConfig,
    SecurityConfig,
)

# Fake MCP clients


class FakeMCPClient:
    """StateProvider + ActionProvider implementation for tests."""

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
                    id=c.id,
                    name=c.name,
                    type=c.type,
                    status=c.status,
                    summary=c.summary,
                    properties={},
                    relationships=[],
                )
        raise ComponentNotFoundError(component_id)

    async def get_system_overview(self, ctx: SessionContext) -> SystemOverview:
        self.calls.append(("get_system_overview", (ctx,), {}))
        return self._overview

    async def execute_action(
        self, ctx: SessionContext, action_name: str, params: dict
    ) -> ActionResult:
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


# Fixtures


@pytest.fixture()
def agents_config():
    return AgentsConfig(
        providers={
            "yandex": ProviderCreds(provider=LlmProvider.YANDEX, api_key="k", yandex_folder="f")
        },
        catalog=[
            ModelEntry(
                id="yandex-gpt-5.1",
                label="YandexGPT 5.1 Pro",
                provider_ref="yandex",
                model="yandexgpt/latest",
            )
        ],
        chat_model="yandex-gpt-5.1",
        intervention_model="yandex-gpt-5.1",
    )


@pytest.fixture()
def config_model(agents_config):
    return ConfigModel(
        database=DatabaseConfig(user="u", password="p", host="h", port=5432, db="d"),
        redis=RedisConfig(url="redis://localhost:6379/0"),
        api=ApiConfig(
            environment="test", jwt_secret="test-secret", frontend_url="http://localhost:3000"
        ),
        log=LogConfig(log_level="DEBUG"),
        agents=agents_config,
        gns3=GNS3Config(
            service_url="http://gns3-service:8101",
            public_url="http://localhost:3080",
            internal_url="http://gns3-server:3080",
        ),
        mcp=MCPConfig(server_url="http://gns3-mcp:8100"),
        security=SecurityConfig(
            cred_encryption_key="r1juy4ePJMqjrYbqXaCw7kDPq8Gwudckyv0wiIBIwfU=",
            internal_api_token="test-internal-token",
        ),
    )


@pytest.fixture()
def fake_mcp():
    return FakeMCPClient()


@pytest.fixture()
def fake_failing_mcp():
    return FakeFailingMCPClient()
