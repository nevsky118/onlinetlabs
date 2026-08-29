# E2E test: GNS3 → MCP → AgentContext → YandexGPT.

import os
import sys

import pytest

from autotests.settings.configuration.env_paths import env_file

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "backend")
    ),
)

try:
    from agents.hint.agent import HintAgent
    from agents.hint.models import HintInput
    from agents.tutor.agent import TutorAgent
    from agents.tutor.models import TutorInput
    from config.env_config_loader import EnvConfigLoader
    from learning_analytics.context import MCPContextBuilder
except ModuleNotFoundError as exc:
    pytest.skip(
        f"backend-зависимости недоступны в окружении автотестов ({exc.name}); "
        "e2e запускать в окружении с зависимостями backend",
        allow_module_level=True,
    )

from autotests.api.api_helpers.e2e.gns3_mcp_helper import GNS3MCPHelper
from autotests.api.data.e2e.learning_analytics_data import HintTestData, MCPContextTestData
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import (
    assert_equal,
    assert_greater_equal,
    assert_true,
)


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPAgentPipelineE2E:
    """E2E tests of the pipeline GNS3 → MCP → AgentContext → LLM."""

    @pytest.fixture(autouse=True)
    def setup(self, config):
        self.helper = GNS3MCPHelper(config)
        self.test_data = MCPContextTestData()

    async def _ensure_project(self):
        """Create a project with nodes. Cleanup goes through EntitiesRegistry."""
        await self.helper.authenticate()
        await self.helper.create_project(self.test_data.project_name)
        await self.helper.create_vpcs_nodes(["PC1", "PC2"])

    @autotest.num("3478")
    @autotest.external_id("33ed8a6f-1427-4ca5-ae78-0c02325d906e")
    @autotest.name("E2E: MCP list_components returns GNS3 project nodes")
    async def test_33ed8a6f_mcp_list_components(self):
        with autotest.step("Prepare GNS3 project"):
            await self._ensure_project()

        with autotest.step("Call MCP list_components"):
            mcp = self.helper.get_mcp_client()
            ctx = self.helper.get_session_context()
            components = await mcp.list_components(ctx)

        with autotest.step("Verify components"):
            assert_greater_equal(len(components), 2, "at least 2 components")
            names = {component.name for component in components}
            assert_true("PC1" in names, "PC1 present")
            assert_true("PC2" in names, "PC2 present")

    @autotest.num("3479")
    @autotest.external_id("9447c714-8252-46c6-b9b3-3941c2f3a573")
    @autotest.name("E2E: MCPContextBuilder builds context from GNS3")
    async def test_9447c714_context_builder(self):
        with autotest.step("Prepare GNS3 project"):
            await self._ensure_project()

        with autotest.step("Build AgentContext"):
            mcp = self.helper.get_mcp_client()
            ctx = self.helper.get_session_context()
            builder = MCPContextBuilder(mcp)
            agent_ctx = await builder.build(
                ctx, None,
                self.test_data.struggle_type,
                self.test_data.dominant_error,
            )

        with autotest.step("Verify context"):
            assert_true(len(agent_ctx.topology_summary) > 0, "topology not empty")
            assert_true("PC1" in agent_ctx.topology_summary, "PC1 in topology")
            assert_equal(agent_ctx.struggle_type, "repeating_errors", "struggle type")

        with autotest.step("to_prompt contains data"):
            prompt = agent_ctx.to_prompt()
            assert_true("СОСТОЯНИЕ СРЕДЫ" in prompt, "header")
            assert_true("PC1" in prompt, "PC1 in prompt")

    @autotest.num("3480")
    @autotest.external_id("752a12bb-29a5-4e0e-91eb-2b7f57744743")
    @autotest.name("E2E: TutorAgent responds with MCP context via YandexGPT")
    async def test_752a12bb_tutor_agent_with_context(self):
        with autotest.step("Prepare GNS3 project"):
            await self._ensure_project()

        with autotest.step("Build context"):
            mcp = self.helper.get_mcp_client()
            ctx = self.helper.get_session_context()
            builder = MCPContextBuilder(mcp)
            agent_ctx = await builder.build(
                ctx, None,
                self.test_data.struggle_type,
                self.test_data.dominant_error,
            )

        with autotest.step("Call TutorAgent"):
            config = EnvConfigLoader().load(str(env_file("backend")))
            tutor = TutorAgent(config, mcp_client=mcp)
            result = await tutor.run(TutorInput(
                session_id="e2e-test",
                user_id="e2e-user",
                question=self.test_data.user_question,
                agent_context=agent_ctx,
            ))

        with autotest.step("Answer is substantive"):
            assert_true(len(result.answer) > 20, "answer longer than 20 characters")

    @autotest.num("3481")
    @autotest.external_id("6f520261-c159-4e1e-bbf9-d0d84f555df8")
    @autotest.name("E2E: HintAgent gives a hint with MCP context")
    async def test_6f520261_hint_agent_with_context(self):
        with autotest.step("Arrange: hint test data with 4 attempts"):
            hint_data = HintTestData(attempts_count=4)

        with autotest.step("Prepare GNS3 project"):
            await self._ensure_project()

        with autotest.step("Build context"):
            mcp = self.helper.get_mcp_client()
            ctx = self.helper.get_session_context()
            builder = MCPContextBuilder(mcp)
            agent_ctx = await builder.build(
                ctx, None,
                "repeating_errors",
                hint_data.last_error,
            )

        with autotest.step("Call HintAgent"):
            config = EnvConfigLoader().load(str(env_file("backend")))
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

        with autotest.step("Hint level 3"):
            assert_equal(result.hint_level, 3, "level 3 at 4 attempts")
            assert_true(len(result.hint) > 10, "hint not empty")
            assert_equal(result.remaining_hints, 0, "no hints remaining")

    @autotest.num("3482")
    @autotest.external_id("2be04b9b-fa9d-47e3-a254-b49383d4ae5c")
    @autotest.name("E2E: get_system_overview returns project summary")
    async def test_2be04b9b_system_overview(self):
        with autotest.step("Prepare GNS3 project"):
            await self._ensure_project()

        with autotest.step("Call MCP get_system_overview"):
            mcp = self.helper.get_mcp_client()
            ctx = self.helper.get_session_context()
            overview = await mcp.get_system_overview(ctx)

        with autotest.step("Verify summary"):
            assert_greater_equal(overview.component_count, 2, "at least 2 components")
            assert_true(len(overview.summary) > 0, "summary not empty")
