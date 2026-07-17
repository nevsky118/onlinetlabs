"""Реальный прогон pydantic-ai Agent.run() (2.x) без мока _agent_for.

TestModel подменяет модель через Agent.override — прогон реальный
(промпт → Agent.run → result.output → Response), сети нет.
"""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.test import TestModel

from agents.hint.agent import HintAgent
from agents.hint.models import HintInput
from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput, TutorResponse
from tests.settings.data.analytics_data import AgentContextData

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestAgentsRunPath:
    """Реальный pydantic-ai Agent.run() через TestModel — проверка совместимости с 2.x."""

    @autotest.num("2520")
    @autotest.external_id("9945ed45-b6be-4aa2-9715-2e5f018e041d")
    @autotest.name("HintAgent: реальный Agent.run через TestModel, кэш модели не портится")
    async def test_9945ed45_hint_real_run_path(self, config_model):
        with autotest.step("Получаем реальный кэшированный pydantic-ai Agent (без мока)"):
            agent = HintAgent(config_model)
            mid = config_model.agents.intervention_model
            pyd_agent = agent._agent_for(mid)
            assert_true(
                isinstance(pyd_agent.model, OpenAIChatModel),
                f"модель до override: {pyd_agent.model}",
            )

        with autotest.step("Реальный run с моделью, подменённой на TestModel"):
            inp = HintInput(
                session_id="s1",
                user_id="u1",
                lab_slug="lab-ospf",
                step_slug="step-1",
                attempts_count=4,
                last_error="OSPF timeout",
                agent_context=AgentContextData().context,
            )
            with pyd_agent.override(
                model=TestModel(custom_output_text="Проверь маршрут OSPF на R1")
            ):
                result = await agent.run(inp, model_id=mid)

        with autotest.step("HintResponse собран из result.output реального прогона"):
            assert_equal(result.hint, "Проверь маршрут OSPF на R1", "hint == canned output")
            assert_equal(result.hint_level, 3, "уровень 3 при 4 попытках")

        with autotest.step(
            "После выхода из override кэш возвращает исходную (не TestModel) модель"
        ):
            cached_again = agent._agent_for(mid)
            assert_true(cached_again is pyd_agent, "Agent закэширован по model_id")
            assert_true(
                isinstance(cached_again.model, OpenAIChatModel),
                f"модель после override: {cached_again.model}",
            )

    @autotest.num("2521")
    @autotest.external_id("75960d89-a54c-4e98-aaa0-6e95629b81ff")
    @autotest.name("TutorAgent: реальный Agent.run через TestModel даёт TutorResponse из output")
    async def test_75960d89_tutor_real_run_path(self, config_model):
        with autotest.step("Получаем реальный кэшированный pydantic-ai Agent (без мока)"):
            agent = TutorAgent(config_model, mcp_client=None)
            mid = config_model.agents.intervention_model
            pyd_agent = agent._agent_for(mid)

        with autotest.step("Реальный run с моделью, подменённой на TestModel"):
            inp = TutorInput(
                session_id="s1",
                user_id="u1",
                question="Почему OSPF не работает?",
                agent_context=AgentContextData().context,
            )
            canned = "OSPF сессия не поднимается из-за неверной маски"
            with pyd_agent.override(model=TestModel(custom_output_text=canned)):
                result = await agent.run(inp, model_id=mid)

        with autotest.step("TutorResponse собран из result.output реального прогона"):
            assert_true(isinstance(result, TutorResponse), f"тип: {type(result)}")
            assert_equal(result.answer, canned, "answer == canned output")
