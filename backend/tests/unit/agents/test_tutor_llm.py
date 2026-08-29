from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from pydantic_ai.models.test import TestModel

from agents.tutor.agent import TutorAgent
from agents.tutor.schemas import TutorInput, TutorResponse
from tests.settings.data.analytics_data import AgentContextData

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestTutorAgentLLM:
    @autotest.num("560")
    @autotest.external_id("77ad961e-74be-494c-9f9f-81712382decd")
    @autotest.name("TutorAgent: LLM failure re-raise, no canned fallback response")
    async def test_77ad961e_run_llm_failure_raises(self, config_model, monkeypatch):
        with autotest.step("Mock LLM raises"):
            agent = TutorAgent(config_model)
            monkeypatch.setattr(
                agent,
                "_agent_for",
                lambda mid, locale: AsyncMock(run=AsyncMock(side_effect=RuntimeError("llm down"))),
            )
            inp = TutorInput(
                session_id="s1",
                user_id="u1",
                question="Что такое OSPF?",
            )

        with autotest.step("Expect re-raise"), pytest.raises(Exception):
            await agent.run(inp)

    @autotest.num("561")
    @autotest.external_id("65e37fbf-3605-4faa-a9d1-65a2ebe1d8b7")
    @autotest.name(
        "TutorAgent: run with agent_context, real Agent.run produces an answer from output"
    )
    async def test_65e37fbf_run_with_context(self, config_model, monkeypatch):
        with autotest.step("Create agent with context, patch _build_model to TestModel"):
            agent = TutorAgent(config_model)
            context = AgentContextData().context
            mid = config_model.agents.intervention_model
            canned = "OSPF сессия не поднимается из-за неверной маски"
            monkeypatch.setattr(
                agent, "_build_model", lambda model_id: TestModel(custom_output_text=canned)
            )
            inp = TutorInput(
                session_id="s1",
                user_id="u1",
                question="Почему OSPF не работает?",
                agent_context=context,
            )

        with autotest.step("Call run (no network, model patched to TestModel)"):
            result = await agent.run(inp, model_id=mid)

        with autotest.step("Answer is built from result.output of a real run"):
            assert_true(isinstance(result, TutorResponse), f"type: {type(result)}")
            assert_equal(result.answer, canned, "answer == canned output")
