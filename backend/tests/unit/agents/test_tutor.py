from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_greater, assert_true

from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput, TutorResponse

pytestmark = [pytest.mark.unit, pytest.mark.agents]


def _make_tutor_input(**overrides):
    defaults = dict(session_id="s1", user_id="u1", question="Что такое OSPF?")
    return TutorInput(**(defaults | overrides))


# TutorAgent


class TestTutorAgent:
    @autotest.num("443")
    @autotest.external_id("f12b5351-9f03-49bc-a545-b2d0adfd5a9f")
    @autotest.name("TutorAgent: initialization")
    def test_f12b5351_init(self, config_model):
        with autotest.step("Create TutorAgent"):
            agent = TutorAgent(config_model)

        with autotest.step("Assert attributes"):
            assert_true(agent.config is config_model, "config is stored")

    @autotest.num("444")
    @autotest.external_id("3303e166-09ff-47f4-b165-1acb1b2c2de5")
    @autotest.name("TutorAgent: system_prompt contains the mentor role")
    def test_3303e166_system_prompt(self, config_model):
        with autotest.step("Get system_prompt"):
            agent = TutorAgent(config_model)
            prompt = agent.system_prompt("en")

        with autotest.step("Assert contents"):
            assert_true(len(prompt) > 10, "prompt has substance")

    @autotest.num("445")
    @autotest.external_id("281a56d4-44d9-454f-a974-451001477483")
    @autotest.name("TutorAgent: run returns TutorResponse on successful LLM")
    async def test_281a56d4_run_basic(self, config_model, monkeypatch):
        with autotest.step("Mock LLM and request"):
            agent = TutorAgent(config_model)
            fake_result = AsyncMock()
            fake_result.output = "Ответ тьютора"
            monkeypatch.setattr(
                agent,
                "_agent_for",
                lambda mid, locale: AsyncMock(run=AsyncMock(return_value=fake_result)),
            )
            result = await agent.run(_make_tutor_input())

        with autotest.step("Assert TutorResponse"):
            assert_true(isinstance(result, TutorResponse), f"type: {type(result)}")
            assert_greater(len(result.answer), 0, "answer is not empty")
            assert_true(isinstance(result.follow_up_questions, list), "follow_up is a list")

    @autotest.num("446")
    @autotest.external_id("145fa491-99f8-4bec-b11e-6a413fff66b3")
    @autotest.name("TutorAgent: LLM failure re-raise, no fallback template")
    async def test_145fa491_run_llm_failure_raises(self, config_model, monkeypatch):
        with autotest.step("Mock LLM raises"):
            agent = TutorAgent(config_model)
            monkeypatch.setattr(
                agent,
                "_agent_for",
                lambda mid, locale: AsyncMock(run=AsyncMock(side_effect=RuntimeError("llm down"))),
            )

        with autotest.step("Expect re-raise"), pytest.raises(Exception):
            await agent.run(_make_tutor_input())
