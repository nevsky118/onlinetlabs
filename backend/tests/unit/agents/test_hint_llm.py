import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from pydantic_ai.models.test import TestModel

from agents.hint.agent import HintAgent
from agents.hint.models import HintInput
from tests.settings.data.analytics_data import AgentContextData

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestHintAgentLLM:
    @autotest.num("570")
    @autotest.external_id("be078385-2caa-42bb-859f-db329a9c64c5")
    @autotest.name("HintAgent: run without agent_context raises ValueError")
    async def test_be078385_run_without_context(self, config_model):
        with autotest.step("Create agent and input without context"):
            agent = HintAgent(config_model)
            inp = HintInput(
                session_id="s1",
                user_id="u1",
                lab_slug="lab-ospf",
                step_slug="step-1",
                attempts_count=0,
            )

        with autotest.step("Expect ValueError"):
            with pytest.raises(ValueError, match="hint requires agent_context"):
                await agent.run(inp)

    @autotest.num("571")
    @autotest.external_id("558d9d41-3c35-46d2-b520-f7c53ce35002")
    @autotest.name("HintAgent: run with agent_context, real Agent.run produces a hint from output")
    async def test_558d9d41_run_with_context(self, config_model, monkeypatch):
        with autotest.step("Create agent with context, patch _build_model to TestModel"):
            agent = HintAgent(config_model)
            context = AgentContextData().context
            mid = config_model.agents.intervention_model
            monkeypatch.setattr(
                agent,
                "_build_model",
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

        with autotest.step("Call run (no network, model patched to TestModel)"):
            result = await agent.run(inp, model_id=mid)

        with autotest.step("Hint is built from result.output of a real run"):
            assert_true(len(result.hint) > 0, "hint is not empty")
            assert_equal(result.hint, "Проверь маршрут OSPF на R1", "hint == canned output")
            assert_equal(result.hint_level, 3, "level 3 at 4 attempts")

    @autotest.num("572")
    @autotest.external_id("a86a10f4-8efa-47c5-b25f-dee13af75ece")
    @autotest.name("HintAgent.system_prompt: contains all 3 levels")
    def test_a86a10f4_system_prompt_levels(self, config_model):
        with autotest.step("Assert prompt contents"):
            prompt = HintAgent(config_model).system_prompt("ru")
            assert_true("Уровень 1" in prompt, "level 1")
            assert_true("Уровень 2" in prompt, "level 2")
            assert_true("Уровень 3" in prompt, "level 3")

    @autotest.num("573")
    @autotest.external_id("ae0197d6-a05d-421b-8d75-8434a4516713")
    @autotest.name("HintAgent: failing_check makes it into the LLM prompt")
    async def test_ae0197d6_failing_check_in_prompt(self, config_model, monkeypatch):
        """Regression FIX 2: failing_check{expected/actual} is visible to the LLM."""
        from unittest.mock import AsyncMock

        agent = HintAgent(config_model)
        context = AgentContextData().context
        captured_prompt: list[str] = []

        async def fake_run(prompt: str):
            captured_prompt.append(prompt)
            r = AsyncMock()
            r.output = "тест"
            return r

        monkeypatch.setattr(agent, "_agent_for", lambda mid, locale: AsyncMock(run=fake_run))
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
        assert captured_prompt, "the LLM was not called"
        prompt = captured_prompt[0]
        assert_true("10.0.0.1/24" in prompt, "expected is in the prompt")
        assert_true("10.0.0.2/24" in prompt, "actual is in the prompt")
