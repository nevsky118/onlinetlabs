from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from pydantic_ai.models.test import TestModel

from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput, TutorResponse
from tests.settings.data.analytics_data import AgentContextData

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestTutorAgentLLM:
    @autotest.num("560")
    @autotest.external_id("a1b2c3d4-e5f6-4789-abcd-560000000001")
    @autotest.name("TutorAgent: LLM failure re-raise, шаблонного ответа нет")
    async def test_a1b2c3d4_run_llm_failure_raises(self, config_model, monkeypatch):
        with autotest.step("Мок LLM выбрасывает"):
            agent = TutorAgent(config_model, mcp_client=None)
            monkeypatch.setattr(
                agent,
                "_agent_for",
                lambda mid: AsyncMock(run=AsyncMock(side_effect=RuntimeError("llm down"))),
            )
            inp = TutorInput(
                session_id="s1",
                user_id="u1",
                question="Что такое OSPF?",
            )

        with autotest.step("Ожидаем re-raise"), pytest.raises(Exception):
            await agent.run(inp)

    @autotest.num("561")
    @autotest.external_id("b2c3d4e5-f6a7-4890-bcde-561000000002")
    @autotest.name("TutorAgent: run с agent_context — реальный Agent.run даёт ответ из output")
    async def test_b2c3d4e5_run_with_context(self, config_model, monkeypatch):
        with autotest.step("Создаём агент с контекстом, подменяем _build_model на TestModel"):
            agent = TutorAgent(config_model, mcp_client=None)
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

        with autotest.step("Вызываем run (без сети — модель подменена на TestModel)"):
            result = await agent.run(inp, model_id=mid)

        with autotest.step("Ответ собран из result.output реального прогона"):
            assert_true(isinstance(result, TutorResponse), f"тип: {type(result)}")
            assert_equal(result.answer, canned, "answer == canned output")
