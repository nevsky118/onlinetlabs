import pytest

from agents.hint.agent import HintAgent, HINT_SYSTEM_PROMPT
from agents.hint.models import HintInput, HintResponse
from tests.settings.data.analytics_data import AgentContextData
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_true, assert_equal

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestHintAgentLLM:
    @autotest.num("570")
    @autotest.external_id("a1b2c3d4-e5f6-4789-abcd-570000000001")
    @autotest.name("HintAgent: run без agent_context — шаблонная подсказка")
    async def test_a1b2c3d4_run_without_context(self, config_model):
        with autotest.step("Создаём агент и вход без контекста"):
            agent = HintAgent(config_model)
            inp = HintInput(
                session_id="s1", user_id="u1",
                lab_slug="lab-ospf", step_slug="step-1",
                attempts_count=0,
            )

        with autotest.step("Вызываем run"):
            result = await agent.run(inp)

        with autotest.step("Шаблонная подсказка"):
            assert_true(isinstance(result, HintResponse), f"тип: {type(result)}")
            assert_equal(result.hint_level, 1, "уровень 1")
            assert_true(len(result.hint) > 0, "подсказка не пустая")

    @autotest.num("571")
    @autotest.external_id("b2c3d4e5-f6a7-4890-bcde-571000000002")
    @autotest.name("HintAgent: run с agent_context — подсказка не пустая")
    async def test_b2c3d4e5_run_with_context(self, config_model):
        with autotest.step("Создаём агент с контекстом"):
            agent = HintAgent(config_model)
            context = AgentContextData().context
            inp = HintInput(
                session_id="s1", user_id="u1",
                lab_slug="lab-ospf", step_slug="step-1",
                attempts_count=4,
                last_error="OSPF timeout",
                agent_context=context,
            )

        with autotest.step("Вызываем run"):
            result = await agent.run(inp)

        with autotest.step("Подсказка не пустая"):
            assert_true(len(result.hint) > 0, "подсказка не пустая")
            assert_equal(result.hint_level, 3, "уровень 3 при 4 попытках")

    @autotest.num("572")
    @autotest.external_id("c3d4e5f6-a7b8-4901-cdef-572000000003")
    @autotest.name("HINT_SYSTEM_PROMPT: содержит все 3 уровня")
    def test_c3d4e5f6_system_prompt_levels(self):
        with autotest.step("Проверяем содержание промпта"):
            assert_true("Уровень 1" in HINT_SYSTEM_PROMPT, "уровень 1")
            assert_true("Уровень 2" in HINT_SYSTEM_PROMPT, "уровень 2")
            assert_true("Уровень 3" in HINT_SYSTEM_PROMPT, "уровень 3")
