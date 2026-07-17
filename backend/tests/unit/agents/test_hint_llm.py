import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from pydantic_ai.models.test import TestModel

from agents.hint.agent import HINT_SYSTEM_PROMPT, HintAgent
from agents.hint.models import HintInput
from tests.settings.data.analytics_data import AgentContextData

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestHintAgentLLM:
    @autotest.num("570")
    @autotest.external_id("a1b2c3d4-e5f6-4789-abcd-570000000001")
    @autotest.name("HintAgent: run без agent_context бросает ValueError")
    async def test_a1b2c3d4_run_without_context(self, config_model):
        with autotest.step("Создаём агент и вход без контекста"):
            agent = HintAgent(config_model)
            inp = HintInput(
                session_id="s1",
                user_id="u1",
                lab_slug="lab-ospf",
                step_slug="step-1",
                attempts_count=0,
            )

        with autotest.step("Ожидаем ValueError"):
            with pytest.raises(ValueError, match="hint requires agent_context"):
                await agent.run(inp)

    @autotest.num("571")
    @autotest.external_id("b2c3d4e5-f6a7-4890-bcde-571000000002")
    @autotest.name("HintAgent: run с agent_context — реальный Agent.run даёт подсказку из output")
    async def test_b2c3d4e5_run_with_context(self, config_model, monkeypatch):
        with autotest.step("Создаём агент с контекстом, подменяем _build_model на TestModel"):
            agent = HintAgent(config_model)
            context = AgentContextData().context
            mid = config_model.agents.intervention_model
            monkeypatch.setattr(
                agent, "_build_model",
                lambda model_id: TestModel(custom_output_text="Проверь маршрут OSPF на R1"),
            )
            inp = HintInput(
                session_id="s1",
                user_id="u1",
                lab_slug="lab-ospf",
                step_slug="step-1",
                attempts_count=4,
                last_error="OSPF timeout",
                agent_context=context,
            )

        with autotest.step("Вызываем run (без сети — модель подменена на TestModel)"):
            result = await agent.run(inp, model_id=mid)

        with autotest.step("Подсказка собрана из result.output реального прогона"):
            assert_true(len(result.hint) > 0, "подсказка не пустая")
            assert_equal(result.hint, "Проверь маршрут OSPF на R1", "hint == canned output")
            assert_equal(result.hint_level, 3, "уровень 3 при 4 попытках")

    @autotest.num("572")
    @autotest.external_id("c3d4e5f6-a7b8-4901-cdef-572000000003")
    @autotest.name("HINT_SYSTEM_PROMPT: содержит все 3 уровня")
    def test_c3d4e5f6_system_prompt_levels(self):
        with autotest.step("Проверяем содержание промпта"):
            assert_true("Уровень 1" in HINT_SYSTEM_PROMPT, "уровень 1")
            assert_true("Уровень 2" in HINT_SYSTEM_PROMPT, "уровень 2")
            assert_true("Уровень 3" in HINT_SYSTEM_PROMPT, "уровень 3")

    @autotest.num("573")
    @autotest.external_id("d4e5f6a7-b8c9-4012-def0-573000000004")
    @autotest.name("HintAgent: failing_check попадает в промпт LLM")
    async def test_d4e5f6a7_failing_check_in_prompt(self, config_model, monkeypatch):
        """Регрессия FIX 2: failing_check{expected/actual} виден LLM."""
        from unittest.mock import AsyncMock

        agent = HintAgent(config_model)
        context = AgentContextData().context
        captured_prompt: list[str] = []

        async def fake_run(prompt: str):
            captured_prompt.append(prompt)
            r = AsyncMock()
            r.output = "тест"
            return r

        monkeypatch.setattr(agent, "_agent_for", lambda mid: AsyncMock(run=fake_run))
        inp = HintInput(
            session_id="s1",
            user_id="u1",
            lab_slug="lab-ospf",
            step_slug="step-1",
            attempts_count=2,
            failing_check={
                "kind": "vpcs_ip",
                "params": {"node": "PC1"},
                "ok": False,
                "expected": "10.0.0.1/24",
                "actual": "10.0.0.2/24",
            },
            agent_context=context,
        )
        await agent.run(inp)
        assert captured_prompt, "LLM не был вызван"
        prompt = captured_prompt[0]
        assert_true("10.0.0.1/24" in prompt, "expected в промпте")
        assert_true("10.0.0.2/24" in prompt, "actual в промпте")
