"""Проверяет: при сбое LLM агенты re-raise, шаблон не возвращается."""

import pytest
from unittest.mock import AsyncMock

from agents.hint.agent import HintAgent
from agents.hint.models import HintInput
from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput
from agents.orchestrator.agent import Orchestrator
from agents.orchestrator.models import InterventionInput
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


async def test_hint_llm_failure_raises(config_model, monkeypatch):
    """HintAgent: LLM exception → re-raise, не шаблон."""
    agent = HintAgent(config_model)
    monkeypatch.setattr(
        agent,
        "_agent_for",
        lambda mid: AsyncMock(run=AsyncMock(side_effect=RuntimeError("llm down"))),
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
    with pytest.raises(Exception):
        await agent.run(inp, "yandex-gpt-5.1")


async def test_hint_no_context_raises(config_model):
    """HintAgent: без agent_context → ValueError."""
    agent = HintAgent(config_model)
    inp = HintInput(
        session_id="s",
        user_id="u",
        lab_slug="l",
        step_slug="connectivity",
        attempts_count=1,
    )
    with pytest.raises(ValueError, match="hint requires agent_context"):
        await agent.run(inp, "yandex-gpt-5.1")


async def test_tutor_llm_failure_raises(config_model, monkeypatch):
    """TutorAgent: LLM exception → re-raise, не шаблон."""
    agent = TutorAgent(config_model)
    monkeypatch.setattr(
        agent,
        "_agent_for",
        lambda mid: AsyncMock(run=AsyncMock(side_effect=RuntimeError("llm down"))),
    )
    inp = TutorInput(session_id="s", user_id="u", question="Что такое OSPF?")
    with pytest.raises(Exception):
        await agent.run(inp, "yandex-gpt-5.1")


async def test_orchestrator_intervene_catches_agent_raise(config_model, monkeypatch):
    """Orchestrator.intervene: agent.run raise → success=False, не исключение."""
    orch = Orchestrator(config_model)

    # Мок агента который бросает
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
    resp = await orch.intervene(inp)
    assert resp.success is False
    assert resp.error is not None
