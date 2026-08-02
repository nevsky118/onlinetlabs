import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_true,
)

from agents.hint.agent import HintAgent
from agents.hint.models import HintInput
from agents.hint.tools import MAX_HINTS, HintTools

pytestmark = [pytest.mark.unit, pytest.mark.agents]


def _make_hint_input(**overrides):
    defaults = dict(
        session_id="s1",
        user_id="u1",
        lab_slug="lab-traceroute",
        step_slug="step-1",
        attempts_count=0,
    )
    return HintInput(**(defaults | overrides))


# HintTools


class TestHintTools:
    @autotest.num("450")
    @autotest.external_id("1a2b3c4d-e5f6-4789-abcd-ef0123456789")
    @autotest.name("HintTools.get_hint_level: level 1 at a low attempt count")
    def test_1a2b3c4d_hint_level_low(self):
        with autotest.step("Assert level at 0-1 attempts"):
            tools = HintTools()
            assert_equal(tools.get_hint_level(0), 1, "0 attempts → level 1")
            assert_equal(tools.get_hint_level(1), 1, "1 attempt → level 1")

    @autotest.num("451")
    @autotest.external_id("2b3c4d5e-f6a7-4890-bcde-f01234567890")
    @autotest.name("HintTools.get_hint_level: level 2 at 2-3 attempts")
    def test_2b3c4d5e_hint_level_mid(self):
        with autotest.step("Assert level at 2-3 attempts"):
            tools = HintTools()
            assert_equal(tools.get_hint_level(2), 2, "2 attempts → level 2")
            assert_equal(tools.get_hint_level(3), 2, "3 attempts → level 2")

    @autotest.num("452")
    @autotest.external_id("3c4d5e6f-a7b8-4901-cdef-012345678901")
    @autotest.name("HintTools.get_hint_level: level 3 at 4+ attempts")
    def test_3c4d5e6f_hint_level_high(self):
        with autotest.step("Assert level at 4+ attempts"):
            tools = HintTools()
            assert_equal(tools.get_hint_level(4), 3, "4 attempts → level 3")
            assert_equal(tools.get_hint_level(10), 3, "10 attempts → level 3")

    @autotest.num("453")
    @autotest.external_id("4d5e6f7a-b8c9-4012-def0-123456789012")
    @autotest.name("HintTools.get_remaining_hints: correct remaining count")
    def test_4d5e6f7a_remaining_hints(self):
        with autotest.step("Assert remaining hints count"):
            tools = HintTools()
            assert_equal(tools.get_remaining_hints(1), MAX_HINTS - 1, "level 1")
            assert_equal(tools.get_remaining_hints(2), MAX_HINTS - 2, "level 2")
            assert_equal(tools.get_remaining_hints(3), 0, "level 3 → 0")

    @autotest.num("454")
    @autotest.external_id("5e6f7a8b-c9d0-4123-ef01-234567890123")
    @autotest.name(
        "HintTools: generate_hint removed, get_hint_level/get_remaining_hints still work"
    )
    def test_5e6f7a8b_no_generate_hint(self):
        tools = HintTools()

        with autotest.step("generate_hint doesn't exist"):
            assert_true(not hasattr(tools, "generate_hint"), "generate_hint removed")

        with autotest.step("get_hint_level and get_remaining_hints are available"):
            assert_equal(tools.get_hint_level(2), 2, "level 2")
            assert_equal(tools.get_remaining_hints(2), 1, "1 remaining")


# HintAgent


class TestHintAgent:
    @autotest.num("455")
    @autotest.external_id("6f7a8b9c-d0e1-4234-f012-345678901234")
    @autotest.name("HintAgent: initialization")
    def test_6f7a8b9c_init(self, config_model):
        with autotest.step("Create HintAgent"):
            agent = HintAgent(config_model)

        with autotest.step("Assert attributes"):
            assert_true(agent.tools is not None, "tools is not None")

    @autotest.num("456")
    @autotest.external_id("7a8b9c0d-e1f2-4345-0123-456789012345")
    @autotest.name("HintAgent: system_prompt contains role")
    def test_7a8b9c0d_system_prompt(self, config_model):
        with autotest.step("Get system_prompt"):
            agent = HintAgent(config_model)
            prompt = agent.system_prompt("en")

        with autotest.step("Assert contents"):
            assert_true(len(prompt) > 10, "prompt has substance")

    @autotest.num("457")
    @autotest.external_id("8b9c0d1e-f2a3-4456-1234-567890123456")
    @autotest.name("HintAgent: run without agent_context raises ValueError")
    async def test_8b9c0d1e_run_no_context_raises(self, config_model):
        with autotest.step("Request a hint without context"):
            agent = HintAgent(config_model)
            with pytest.raises(ValueError, match="hint requires agent_context"):
                await agent.run(_make_hint_input(attempts_count=0))

    @autotest.num("458")
    @autotest.external_id("9c0d1e2f-a3b4-4567-2345-678901234567")
    @autotest.name("HintAgent: hint level is determined by attempt count")
    def test_9c0d1e2f_hint_level_by_attempts(self, config_model):
        with autotest.step("Assert level at 5 attempts"):
            agent = HintAgent(config_model)
            assert_equal(agent.tools.get_hint_level(5), 3, "level 3")
            assert_equal(agent.tools.get_remaining_hints(3), 0, "no hints remaining")
