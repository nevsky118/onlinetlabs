import pytest

from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput, TutorResponse
from tests.settings.data.analytics_data import AgentContextData
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_true

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestTutorAgentLLM:
    @autotest.num("560")
    @autotest.external_id("a1b2c3d4-e5f6-4789-abcd-560000000001")
    @autotest.name("TutorAgent: run без agent_context — fallback ответ")
    async def test_a1b2c3d4_run_without_context(self, config_model):
        with autotest.step("Создаём агент и вход без контекста"):
            agent = TutorAgent(config_model, mcp_client=None)
            inp = TutorInput(
                session_id="s1", user_id="u1",
                question="Что такое OSPF?",
            )

        with autotest.step("Вызываем run"):
            result = await agent.run(inp)

        with autotest.step("Ответ не пустой"):
            assert_true(isinstance(result, TutorResponse), f"тип: {type(result)}")
            assert_true(len(result.answer) > 0, "ответ не пустой")

    @autotest.num("561")
    @autotest.external_id("b2c3d4e5-f6a7-4890-bcde-561000000002")
    @autotest.name("TutorAgent: run с agent_context — ответ не пустой")
    async def test_b2c3d4e5_run_with_context(self, config_model):
        with autotest.step("Создаём агент с контекстом"):
            agent = TutorAgent(config_model, mcp_client=None)
            context = AgentContextData().context
            inp = TutorInput(
                session_id="s1", user_id="u1",
                question="Почему OSPF не работает?",
                agent_context=context,
            )

        with autotest.step("Вызываем run"):
            result = await agent.run(inp)

        with autotest.step("Ответ не пустой"):
            assert_true(isinstance(result, TutorResponse), f"тип: {type(result)}")
            assert_true(len(result.answer) > 0, "ответ не пустой")
