from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true

from agents.hint.schemas import HintResponse
from agents.orchestrator.agent import Orchestrator
from agents.orchestrator.router import INTENT_TO_AGENT, resolve_agent


def _mock_hint_agent(orch):
    """Returns a HintResponse without an LLM call."""
    fake = AsyncMock()
    fake.run = AsyncMock(
        return_value=HintResponse(hint="подсказка", hint_level=2, remaining_hints=1)
    )
    orch._agents["hint"] = fake


pytestmark = [pytest.mark.unit, pytest.mark.agents]


# Router


class TestRouter:
    @autotest.num("460")
    @autotest.external_id("3a1c644b-b32e-48cf-bc93-f116c135abc1")
    @autotest.name("resolve_agent: all known intents")
    def test_3a1c644b_resolve_known_intents(self):
        with autotest.step("Assert mapping"):
            for intent, agent_name in INTENT_TO_AGENT.items():
                result = resolve_agent(intent)
                assert_equal(result, agent_name, f"intent={intent} → {agent_name}")

    @autotest.num("461")
    @autotest.external_id("e156dc05-c6d1-4018-9d2a-9ae707bc5f6b")
    @autotest.name("resolve_agent: unknown intent → None")
    def test_e156dc05_resolve_unknown_intent(self):
        with autotest.step("Assert unknown"):
            result = resolve_agent("unknown_intent")
            assert_is_none(result, "unknown intent → None")


# Orchestrator


class TestOrchestrator:
    @autotest.num("462")
    @autotest.external_id("ce96764d-cb45-4f43-95cd-11d671297249")
    @autotest.name("Orchestrator: initialization")
    def test_ce96764d_init(self, config_model):
        with autotest.step("Create Orchestrator"):
            orch = Orchestrator(config_model, db=None)

        with autotest.step("Assert attributes"):
            assert_equal(orch.config, config_model, "config")
            assert_equal(orch._agents, {}, "agents is empty")


from agents.orchestrator.schemas import InterventionInput


class TestOrchestratorIntervene:
    @autotest.num("470")
    @autotest.external_id("c0d1e2f3-a4b5-4c6d-8e7f-a0b1c2d3e4f5")
    @autotest.name("InterventionInput: model construction")
    def test_c0d1e2f3_intervention_input_model(self):
        with autotest.step("Create InterventionInput"):
            inp = InterventionInput(
                session_id="s1",
                user_id="u1",
                intervention_type="hint",
                context={"struggle_type": "repeating_errors", "dominant_error": "bad ip"},
            )

        with autotest.step("Assert fields"):
            assert_equal(inp.intervention_type, "hint", "intervention type")
            assert_equal(inp.session_id, "s1", "session_id")

    @autotest.num("471")
    @autotest.external_id("e86a32fb-e590-409c-b6a6-e61728963738")
    @autotest.name("Orchestrator.intervene: routes to hint agent")
    async def test_e86a32fb_intervene_routes_to_hint(self, config_model):
        with autotest.step("Create Orchestrator and InterventionInput with a mock agent"):
            orch = Orchestrator(config_model, db=None)
            _mock_hint_agent(orch)
            inp = InterventionInput(
                session_id="s1",
                user_id="u1",
                intervention_type="hint",
                context={"step_slug": "step-1", "attempts_count": 3, "lab_slug": "lab-1"},
            )

        with autotest.step("Call intervene"):
            result = await orch.intervene(inp)

        with autotest.step("Assert result"):
            assert_true(result.success, "success=True")
            assert_equal(result.agent_used, "hint", "agent: hint")
