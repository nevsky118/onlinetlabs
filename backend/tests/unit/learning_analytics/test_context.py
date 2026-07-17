from datetime import UTC, datetime

import pytest
from mcp_sdk.models import Component, ErrorEntry, LogLevel, UserAction
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from learning_analytics.context import AgentContext, MCPContextBuilder

pytestmark = [pytest.mark.unit]


class FakeContextMCPClient:
    """Fake MCP for context-builder tests."""

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
    @autotest.external_id("44f74056-027a-4293-b00c-0e500dee5d38")
    @autotest.name("AgentContext.to_prompt: форматирует контекст")
    def test_44f74056_to_prompt(self):
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
    @autotest.external_id("468c37ba-9575-4399-aef8-423e249b9902")
    @autotest.name("AgentContext.to_prompt: пустой контекст не падает")
    def test_468c37ba_to_prompt_empty(self):
        with autotest.step("Создаём пустой AgentContext"):
            ctx = AgentContext(
                topology_summary="",
                recent_errors=[],
                recent_actions=[],
                struggle_type=None,
                dominant_error=None,
                features_summary="",
            )

        with autotest.step("to_prompt возвращает строку"):
            prompt = ctx.to_prompt()
            assert_true(isinstance(prompt, str), "строка")


class TestMCPContextBuilder:
    @autotest.num("552")
    @autotest.external_id("c362feb3-de89-49b5-b627-cc4daec9ee89")
    @autotest.name("MCPContextBuilder.build: собирает контекст из MCP")
    async def test_c362feb3_build(self):
        now = datetime.now(tz=UTC)
        with autotest.step("Создаём фейк MCP с данными"):
            mcp = FakeContextMCPClient(
                components=[
                    Component(id="n1", name="R1", type="qemu", status="running", summary=""),
                    Component(id="n2", name="R2", type="qemu", status="stopped", summary=""),
                ],
                actions=[
                    UserAction(
                        timestamp=now,
                        component_id="n1",
                        action="start_node",
                        raw_command=None,
                        success=True,
                    ),
                ],
                errors=[
                    ErrorEntry(
                        timestamp=now,
                        level=LogLevel.ERROR,
                        message="OSPF timeout",
                        component_id="n2",
                    ),
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
    @autotest.external_id("be858141-1e28-43dc-809b-062c505903e0")
    @autotest.name("MCPContextBuilder.build: MCP недоступен → пустой контекст")
    async def test_be858141_build_mcp_down(self):
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
