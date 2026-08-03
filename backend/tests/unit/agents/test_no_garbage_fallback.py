"""Checks: on LLM failure, agents re-raise instead of returning a canned template."""

from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest

from agents.hint.agent import HintAgent
from agents.hint.models import HintInput
from agents.orchestrator.agent import Orchestrator
from agents.orchestrator.models import InterventionInput
from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput
from learning_analytics.context import AgentContext

pytestmark = [pytest.mark.unit, pytest.mark.agents]


def _hint_context() -> AgentContext:
    return AgentContext(
        topology_summary="R1, PC1",
        recent_errors=["ping failed"],
        recent_actions=[],
        struggle_type="repeating_errors",
        dominant_error="ping failed",
        features_summary="",
    )


@autotest.num("3209")
@autotest.external_id("c230cf00-73a4-4ae8-aa82-91233dec57f0")
@autotest.name("HintAgent.run: re-raises on LLM failure instead of a canned fallback")
async def test_c230cf00_hint_llm_failure_raises(config_model, monkeypatch):
    """HintAgent: LLM exception → re-raise, not a canned template."""
    with autotest.step("Arrange: HintAgent whose inner LLM call raises"):
        agent = HintAgent(config_model)
        monkeypatch.setattr(
            agent,
            "_agent_for",
            lambda mid, locale: AsyncMock(run=AsyncMock(side_effect=RuntimeError("llm down"))),
        )
        inp = HintInput(
            session_id="s",
            user_id="u",
            lab_slug="l",
            step_slug="connectivity",
            attempts_count=3,
            last_error="ping failed",
            agent_context=_hint_context(),
        )

    with autotest.step("Act+Assert: run re-raises instead of returning a fallback"):
        with pytest.raises(Exception):
            await agent.run(inp, "yandex-gpt-5.1")


@autotest.num("3210")
@autotest.external_id("8eb78cde-892b-44bc-9b16-7aab207b3e24")
@autotest.name("HintAgent.run: raises ValueError when agent_context is missing")
async def test_8eb78cde_hint_no_context_raises(config_model):
    """HintAgent: without agent_context → ValueError."""
    with autotest.step("Arrange: HintAgent and an input missing agent_context"):
        agent = HintAgent(config_model)
        inp = HintInput(
            session_id="s",
            user_id="u",
            lab_slug="l",
            step_slug="connectivity",
            attempts_count=1,
        )

    with autotest.step("Act+Assert: run raises ValueError('hint requires agent_context')"):
        with pytest.raises(ValueError, match="hint requires agent_context"):
            await agent.run(inp, "yandex-gpt-5.1")


@autotest.num("3211")
@autotest.external_id("efd15bff-262e-4525-a0a5-9da3e4fd8229")
@autotest.name("TutorAgent.run: re-raises on LLM failure instead of a canned fallback")
async def test_efd15bff_tutor_llm_failure_raises(config_model, monkeypatch):
    """TutorAgent: LLM exception → re-raise, not a canned template."""
    with autotest.step("Arrange: TutorAgent whose inner LLM call raises"):
        agent = TutorAgent(config_model)
        monkeypatch.setattr(
            agent,
            "_agent_for",
            lambda mid, locale: AsyncMock(run=AsyncMock(side_effect=RuntimeError("llm down"))),
        )
        inp = TutorInput(session_id="s", user_id="u", question="Что такое OSPF?")

    with autotest.step("Act+Assert: run re-raises instead of returning a fallback"):
        with pytest.raises(Exception):
            await agent.run(inp, "yandex-gpt-5.1")


@autotest.num("3212")
@autotest.external_id("3f542499-2d86-40eb-a77e-5180a3bbed38")
@autotest.name("Orchestrator.intervene: catches agent exceptions and returns success=False")
async def test_3f542499_orchestrator_intervene_catches_agent_raise(config_model, monkeypatch):
    """Orchestrator.intervene: agent.run raise → success=False, not an exception."""
    with autotest.step("Arrange: Orchestrator whose selected agent raises"):
        orch = Orchestrator(config_model)

        # Mock an agent that raises
        fake_agent = AsyncMock()
        fake_agent.run = AsyncMock(side_effect=RuntimeError("llm down"))
        monkeypatch.setattr(orch, "_get_agent", lambda name: fake_agent)

        inp = InterventionInput(
            session_id="s",
            user_id="u",
            intervention_type="hint",
            context={
                "lab_slug": "l",
                "step_slug": "connectivity",
                "attempts_count": 3,
                "last_error": "ping failed",
                "agent_context": _hint_context().model_dump(),
            },
        )

    with autotest.step("Act: intervene"):
        resp = await orch.intervene(inp)

    with autotest.step("Assert: response is success=False with an error message"):
        assert resp.success is False
        assert resp.error is not None
