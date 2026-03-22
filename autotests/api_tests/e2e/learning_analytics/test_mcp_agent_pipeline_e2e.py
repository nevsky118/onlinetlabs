# E2E тест: GNS3 → MCP → AgentContext → YandexGPT.

import sys

import pytest

sys.path.insert(0, "backend")

from agents.hint.agent import HintAgent
from agents.hint.models import HintInput
from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput
from autotests.api.api_helpers.e2e.gns3_mcp_helper import GNS3MCPHelper
from autotests.api.data.e2e.learning_analytics_data import HintTestData, MCPContextTestData
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import (
    assert_equal,
    assert_greater_equal,
    assert_true,
)
from config.env_config_loader import EnvConfigLoader
from learning_analytics.context import MCPContextBuilder


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPAgentPipelineE2E:
    """E2E тесты пайплайна: GNS3 → MCP → AgentContext → LLM."""

    @pytest.fixture(autouse=True)
    def setup(self, config):
        self.helper = GNS3MCPHelper(config)
        self.test_data = MCPContextTestData()

    async def _ensure_project(self):
        """Создать проект с нодами. Очистка через EntitiesRegistry."""
        await self.helper.authenticate()
        await self.helper.create_project(self.test_data.project_name)
        await self.helper.create_vpcs_nodes(["PC1", "PC2"])

    @autotest.num("700")
    @autotest.external_id("a1b2c3d4-e5f6-4789-abcd-700000000001")
    @autotest.name("E2E: MCP list_components возвращает ноды GNS3 проекта")
    async def test_a1b2c3d4_mcp_list_components(self):
        with autotest.step("Подготовка GNS3 проекта"):
            await self._ensure_project()

        with autotest.step("Вызываем MCP list_components"):
            mcp = self.helper.get_mcp_client()
            ctx = self.helper.get_session_context()
            components = await mcp.list_components(ctx)

        with autotest.step("Проверяем компоненты"):
            assert_greater_equal(len(components), 2, "минимум 2 компонента")
            names = {c.name for c in components}
            assert_true("PC1" in names, "PC1 присутствует")
            assert_true("PC2" in names, "PC2 присутствует")

    @autotest.num("701")
    @autotest.external_id("b2c3d4e5-f6a7-4890-bcde-701000000002")
    @autotest.name("E2E: MCPContextBuilder собирает контекст из GNS3")
    async def test_b2c3d4e5_context_builder(self):
        with autotest.step("Подготовка GNS3 проекта"):
            await self._ensure_project()

        with autotest.step("Собираем AgentContext"):
            mcp = self.helper.get_mcp_client()
            ctx = self.helper.get_session_context()
            builder = MCPContextBuilder(mcp)
            agent_ctx = await builder.build(
                ctx, None,
                self.test_data.struggle_type,
                self.test_data.dominant_error,
            )

        with autotest.step("Проверяем контекст"):
            assert_true(len(agent_ctx.topology_summary) > 0, "топология не пустая")
            assert_true("PC1" in agent_ctx.topology_summary, "PC1 в топологии")
            assert_equal(agent_ctx.struggle_type, "repeating_errors", "тип struggle")

        with autotest.step("to_prompt содержит данные"):
            prompt = agent_ctx.to_prompt()
            assert_true("СОСТОЯНИЕ СРЕДЫ" in prompt, "заголовок")
            assert_true("PC1" in prompt, "PC1 в промпте")

    @autotest.num("702")
    @autotest.external_id("c3d4e5f6-a7b8-4901-cdef-702000000003")
    @autotest.name("E2E: TutorAgent отвечает с MCP контекстом через YandexGPT")
    async def test_c3d4e5f6_tutor_agent_with_context(self):
        with autotest.step("Подготовка GNS3 проекта"):
            await self._ensure_project()

        with autotest.step("Собираем контекст"):
            mcp = self.helper.get_mcp_client()
            ctx = self.helper.get_session_context()
            builder = MCPContextBuilder(mcp)
            agent_ctx = await builder.build(
                ctx, None,
                self.test_data.struggle_type,
                self.test_data.dominant_error,
            )

        with autotest.step("Вызываем TutorAgent"):
            config = EnvConfigLoader().load("../backend/local.env")
            tutor = TutorAgent(config, mcp_client=mcp)
            result = await tutor.run(TutorInput(
                session_id="e2e-test",
                user_id="e2e-user",
                question=self.test_data.user_question,
                agent_context=agent_ctx,
            ))

        with autotest.step("Ответ содержателен"):
            assert_true(len(result.answer) > 20, "ответ больше 20 символов")

    @autotest.num("703")
    @autotest.external_id("d4e5f6a7-b8c9-4012-defa-703000000004")
    @autotest.name("E2E: HintAgent выдаёт подсказку с MCP контекстом")
    async def test_d4e5f6a7_hint_agent_with_context(self):
        hint_data = HintTestData(attempts_count=4)

        with autotest.step("Подготовка GNS3 проекта"):
            await self._ensure_project()

        with autotest.step("Собираем контекст"):
            mcp = self.helper.get_mcp_client()
            ctx = self.helper.get_session_context()
            builder = MCPContextBuilder(mcp)
            agent_ctx = await builder.build(
                ctx, None,
                "repeating_errors",
                hint_data.last_error,
            )

        with autotest.step("Вызываем HintAgent"):
            config = EnvConfigLoader().load("../backend/local.env")
            hint_agent = HintAgent(config)
            result = await hint_agent.run(HintInput(
                session_id="e2e-test",
                user_id="e2e-user",
                lab_slug="ospf-vlan-lab",
                step_slug=hint_data.step_slug,
                attempts_count=hint_data.attempts_count,
                last_error=hint_data.last_error,
                agent_context=agent_ctx,
            ))

        with autotest.step("Подсказка уровня 3"):
            assert_equal(result.hint_level, 3, "уровень 3 при 4 попытках")
            assert_true(len(result.hint) > 10, "подсказка не пустая")
            assert_equal(result.remaining_hints, 0, "подсказок не осталось")

    @autotest.num("704")
    @autotest.external_id("e5f6a7b8-c9d0-4123-efab-704000000005")
    @autotest.name("E2E: get_system_overview возвращает сводку проекта")
    async def test_e5f6a7b8_system_overview(self):
        with autotest.step("Подготовка GNS3 проекта"):
            await self._ensure_project()

        with autotest.step("Вызываем MCP get_system_overview"):
            mcp = self.helper.get_mcp_client()
            ctx = self.helper.get_session_context()
            overview = await mcp.get_system_overview(ctx)

        with autotest.step("Проверяем сводку"):
            assert_greater_equal(overview.component_count, 2, "минимум 2 компонента")
            assert_true(len(overview.summary) > 0, "summary не пустой")
