"""Real pydantic-ai Agent.run() (2.x) execution without mocking Agent.run.

_build_model is swapped for TestModel, the run is real
(prompt -> Agent.run -> result.output -> Response), no network involved.
_agent_for no longer caches the Agent by model_id (pydantic-ai 2.x gets the
model per-run), so TestModel is substituted via _build_model.
"""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from pydantic_ai.models.test import TestModel

from agents.hint.agent import HintAgent
from agents.hint.models import HintInput
from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput, TutorResponse
from tests.settings.data.analytics_data import AgentContextData

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestAgentsRunPath:
    """Real pydantic-ai Agent.run() via TestModel, checks compatibility with 2.x."""

    @autotest.num("2520")
    @autotest.external_id("9945ed45-b6be-4aa2-9715-2e5f018e041d")
    @autotest.name("HintAgent: реальный Agent.run через TestModel (без кэша Agent по model_id)")
    async def test_9945ed45_hint_real_run_path(self, config_model, monkeypatch):
        with autotest.step("Создаём HintAgent, подменяем _build_model на TestModel"):
            agent = HintAgent(config_model)
            mid = config_model.agents.intervention_model
            monkeypatch.setattr(
                agent,
                "_build_model",
                lambda model_id: TestModel(custom_output_text="Проверь маршрут OSPF на R1"),
            )

        with autotest.step("Реальный run через Agent.run с TestModel"):
            inp = HintInput(
                session_id="s1",
                user_id="u1",
                lab_slug="lab-ospf",
                step_slug="step-1",
                attempts_count=4,
                last_error="OSPF timeout",
                agent_context=AgentContextData().context,
            )
            result = await agent.run(inp, model_id=mid)

        with autotest.step("HintResponse собран из result.output реального прогона"):
            assert_equal(result.hint, "Проверь маршрут OSPF на R1", "hint == canned output")
            assert_equal(result.hint_level, 3, "уровень 3 при 4 попытках")

        with autotest.step("Повторный run с тем же model_id снова строит Agent с нужной моделью"):
            result_again = await agent.run(inp, model_id=mid)
            assert_true(
                result_again.hint == result.hint,
                "без кэша Agent-инстансов результат стабилен между вызовами",
            )

    @autotest.num("2521")
    @autotest.external_id("75960d89-a54c-4e98-aaa0-6e95629b81ff")
    @autotest.name("TutorAgent: реальный Agent.run через TestModel даёт TutorResponse из output")
    async def test_75960d89_tutor_real_run_path(self, config_model, monkeypatch):
        with autotest.step("Создаём TutorAgent, подменяем _build_model на TestModel"):
            agent = TutorAgent(config_model, mcp_client=None)
            mid = config_model.agents.intervention_model
            canned = "OSPF сессия не поднимается из-за неверной маски"
            monkeypatch.setattr(
                agent,
                "_build_model",
                lambda model_id: TestModel(custom_output_text=canned),
            )

        with autotest.step("Реальный run через Agent.run с TestModel"):
            inp = TutorInput(
                session_id="s1",
                user_id="u1",
                question="Почему OSPF не работает?",
                agent_context=AgentContextData().context,
            )
            result = await agent.run(inp, model_id=mid)

        with autotest.step("TutorResponse собран из result.output реального прогона"):
            assert_true(isinstance(result, TutorResponse), f"тип: {type(result)}")
            assert_equal(result.answer, canned, "answer == canned output")
