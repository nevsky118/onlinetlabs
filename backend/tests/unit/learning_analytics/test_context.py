import pytest
from datetime import datetime, timezone

from learning_analytics.context import AgentContext, MCPContextBuilder
from mcp_sdk.models import Component, UserAction, ErrorEntry, LogLevel
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class FakeContextMCPClient:
    """Фейк MCP для тестов контекст-билдера."""

    def __init__(self, components=None, actions=None, errors=None):
        self._components = components or []
        self._actions = actions or []
        self._errors = errors or []

    async def list_components(self, ctx):
        return self._components

    async def list_user_actions(self, ctx, limit=10):
        return self._actions[:limit]

    async def list_errors(self, ctx, since=None):
        return self._errors


class TestAgentContext:
    @autotest.num("550")
    @autotest.external_id("a1b2c3d4-e5f6-4789-abcd-550000000001")
    @autotest.name("AgentContext.to_prompt: форматирует контекст")
    def test_a1b2c3d4_to_prompt(self):
        with autotest.step("Создаём AgentContext"):
            ctx = AgentContext(
                topology_summary="2 ноды (R1 running, R2 stopped), 1 линк",
                recent_errors=["Interface Gi0/0 down"],
                recent_actions=["start_node(R1)", "create_link(R1→R2)"],
                struggle_type="repeating_errors",
                dominant_error="Interface Gi0/0 down",
                features_summary="10 событий, 3 повтора ошибки",
            )

        with autotest.step("Проверяем to_prompt"):
            prompt = ctx.to_prompt()
            assert_true("R1 running" in prompt, "содержит топологию")
            assert_true("Interface Gi0/0 down" in prompt, "содержит ошибку")
            assert_true("repeating_errors" in prompt, "содержит тип struggle")

    @autotest.num("551")
    @autotest.external_id("b2c3d4e5-f6a7-4890-bcde-551000000002")
    @autotest.name("AgentContext.to_prompt: пустой контекст не падает")
    def test_b2c3d4e5_to_prompt_empty(self):
        with autotest.step("Создаём пустой AgentContext"):
            ctx = AgentContext(
                topology_summary="", recent_errors=[], recent_actions=[],
                struggle_type=None, dominant_error=None, features_summary="",
            )

        with autotest.step("to_prompt возвращает строку"):
            prompt = ctx.to_prompt()
            assert_true(isinstance(prompt, str), "строка")


class TestMCPContextBuilder:
    @autotest.num("552")
    @autotest.external_id("c3d4e5f6-a7b8-4901-cdef-552000000003")
    @autotest.name("MCPContextBuilder.build: собирает контекст из MCP")
    async def test_c3d4e5f6_build(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём фейк MCP с данными"):
            mcp = FakeContextMCPClient(
                components=[
                    Component(id="n1", name="R1", type="qemu", status="running", summary=""),
                    Component(id="n2", name="R2", type="qemu", status="stopped", summary=""),
                ],
                actions=[
                    UserAction(timestamp=now, component_id="n1", action="start_node", raw_command=None, success=True),
                ],
                errors=[
                    ErrorEntry(timestamp=now, level=LogLevel.ERROR, message="OSPF timeout", component_id="n2"),
                ],
            )
            builder = MCPContextBuilder(mcp)

        with autotest.step("Собираем контекст"):
            ctx = await builder.build(None, None, "repeating_errors", "OSPF timeout")

        with autotest.step("Проверяем AgentContext"):
            assert_true("R1" in ctx.topology_summary, "содержит R1")
            assert_equal(len(ctx.recent_errors), 1, "1 ошибка")
            assert_equal(ctx.struggle_type, "repeating_errors", "тип struggle")

    @autotest.num("553")
    @autotest.external_id("d4e5f6a7-b8c9-4012-defa-553000000004")
    @autotest.name("MCPContextBuilder.build: MCP недоступен → пустой контекст")
    async def test_d4e5f6a7_build_mcp_down(self):
        with autotest.step("Создаём MCP который бросает исключения"):
            class FailingMCP:
                async def list_components(self, ctx):
                    raise ConnectionError("MCP down")
                async def list_user_actions(self, ctx, limit=10):
                    raise ConnectionError("MCP down")
                async def list_errors(self, ctx, since=None):
                    raise ConnectionError("MCP down")

            builder = MCPContextBuilder(FailingMCP())

        with autotest.step("build не падает"):
            ctx = await builder.build(None, None, None, None)

        with autotest.step("Контекст пустой но валидный"):
            assert_equal(ctx.topology_summary, "", "пустая топология")
            assert_equal(ctx.recent_errors, [], "нет ошибок")
