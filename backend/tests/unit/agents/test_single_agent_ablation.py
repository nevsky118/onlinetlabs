"""#7 extra: single-vs-multi-agent ablation — the intervention routing toggle."""

from unittest.mock import MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from agents.orchestrator.agent import Orchestrator
from agents.orchestrator.models import InterventionInput

pytestmark = [pytest.mark.unit]


class TestSingleAgentAblation:
    @autotest.num("2005")
    @autotest.external_id("55d750d4-5c0b-47db-83a9-4c39813fd497")
    @autotest.name("Single-agent mode: intervene форсит generalist intervene_tutor")
    async def test_55d750d4_single_mode_routes_to_tutor(self, config_model):
        with autotest.step("Arrange: single_agent_mode=True, intervention_type=simplify"):
            config_model.learning_analytics.single_agent_mode = True
            orch = Orchestrator(config_model)
            inp = InterventionInput(
                session_id="s1",
                user_id="u1",
                intervention_type="simplify",
                context={},
            )

        with autotest.step("Act: intervene (resolve_agent замокан → None, ловим имя маршрута)"):
            with patch(
                "agents.orchestrator.agent.resolve_agent", MagicMock(return_value=None)
            ) as ra:
                await orch.intervene(inp)

        with autotest.step("Assert: маршрут форсирован на intervene_tutor"):
            assert_equal(ra.call_args.args[0], "intervene_tutor", "single mode → intervene_tutor")

    @autotest.num("2006")
    @autotest.external_id("6d88f4f3-f188-4e2b-9f96-1fb9fae5733c")
    @autotest.name("Multi-agent (default): intervene маршрутизирует по типу затруднения")
    async def test_6d88f4f3_multi_mode_routes_by_type(self, config_model):
        with autotest.step("Arrange: single_agent_mode=False (дефолт), type=simplify"):
            orch = Orchestrator(config_model)
            inp = InterventionInput(
                session_id="s1",
                user_id="u1",
                intervention_type="simplify",
                context={},
            )

        with autotest.step("Act: intervene"):
            with patch(
                "agents.orchestrator.agent.resolve_agent", MagicMock(return_value=None)
            ) as ra:
                await orch.intervene(inp)

        with autotest.step("Assert: маршрут по типу intervene_simplify"):
            assert_equal(ra.call_args.args[0], "intervene_simplify", "multi → по типу")
