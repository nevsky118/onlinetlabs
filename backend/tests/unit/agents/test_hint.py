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
    @autotest.external_id("1adbc260-353d-47d0-a7c4-a791465b2c28")
    @autotest.name("HintTools.get_hint_level: level 1 at a low attempt count")
    def test_1adbc260_hint_level_low(self):
        with autotest.step("Assert level at 0-1 attempts"):
            tools = HintTools()
            assert_equal(tools.get_hint_level(0), 1, "0 attempts → level 1")
            assert_equal(tools.get_hint_level(1), 1, "1 attempt → level 1")

    @autotest.num("451")
    @autotest.external_id("c6176e1f-ff17-4788-937e-476ecdaab53f")
    @autotest.name("HintTools.get_hint_level: level 2 at 2-3 attempts")
    def test_c6176e1f_hint_level_mid(self):
        with autotest.step("Assert level at 2-3 attempts"):
            tools = HintTools()
            assert_equal(tools.get_hint_level(2), 2, "2 attempts → level 2")
            assert_equal(tools.get_hint_level(3), 2, "3 attempts → level 2")

    @autotest.num("452")
    @autotest.external_id("2fea7118-24bf-4974-b2de-e57b0d5993a2")
    @autotest.name("HintTools.get_hint_level: level 3 at 4+ attempts")
    def test_2fea7118_hint_level_high(self):
        with autotest.step("Assert level at 4+ attempts"):
            tools = HintTools()
            assert_equal(tools.get_hint_level(4), 3, "4 attempts → level 3")
            assert_equal(tools.get_hint_level(10), 3, "10 attempts → level 3")

    @autotest.num("453")
    @autotest.external_id("bc5b86e0-9dfc-48ba-be3f-7f991c9445a4")
    @autotest.name("HintTools.get_remaining_hints: correct remaining count")
    def test_bc5b86e0_remaining_hints(self):
        with autotest.step("Assert remaining hints count"):
            tools = HintTools()
            assert_equal(tools.get_remaining_hints(1), MAX_HINTS - 1, "level 1")
            assert_equal(tools.get_remaining_hints(2), MAX_HINTS - 2, "level 2")
            assert_equal(tools.get_remaining_hints(3), 0, "level 3 → 0")

    @autotest.num("454")
    @autotest.external_id("c6583f2d-b43e-4abe-9992-464ca6354a0c")
    @autotest.name(
        "HintTools: generate_hint removed, get_hint_level/get_remaining_hints still work"
    )
    def test_c6583f2d_no_generate_hint(self):
        with autotest.step("Arrange: create HintTools"):
            tools = HintTools()

        with autotest.step("generate_hint doesn't exist"):
            assert_true(not hasattr(tools, "generate_hint"), "generate_hint removed")

        with autotest.step("get_hint_level and get_remaining_hints are available"):
            assert_equal(tools.get_hint_level(2), 2, "level 2")
            assert_equal(tools.get_remaining_hints(2), 1, "1 remaining")


# HintAgent


class TestHintAgent:
    @autotest.num("455")
    @autotest.external_id("4b7ef3d4-652e-4d61-a555-fcbacb16a97c")
    @autotest.name("HintAgent: initialization")
    def test_4b7ef3d4_init(self, config_model):
        with autotest.step("Create HintAgent"):
            agent = HintAgent(config_model)

        with autotest.step("Assert attributes"):
            assert_true(agent.tools is not None, "tools is not None")

    @autotest.num("456")
    @autotest.external_id("bd42dda6-7c12-4f43-afeb-846ae47bd5c7")
    @autotest.name("HintAgent: system_prompt contains role")
    def test_bd42dda6_system_prompt(self, config_model):
        with autotest.step("Get system_prompt"):
            agent = HintAgent(config_model)
            prompt = agent.system_prompt("en")

        with autotest.step("Assert contents"):
            assert_true(len(prompt) > 10, "prompt has substance")

    @autotest.num("457")
    @autotest.external_id("8b80f85e-7615-4d5c-83e1-3c850741e8a6")
    @autotest.name("HintAgent: run without agent_context raises ValueError")
    async def test_8b80f85e_run_no_context_raises(self, config_model):
        with autotest.step("Request a hint without context"):
            agent = HintAgent(config_model)
            with pytest.raises(ValueError, match="hint requires agent_context"):
                await agent.run(_make_hint_input(attempts_count=0))

    @autotest.num("458")
    @autotest.external_id("df9ed3b6-301b-4767-ad94-8f641f745933")
    @autotest.name("HintAgent: hint level is determined by attempt count")
    def test_df9ed3b6_hint_level_by_attempts(self, config_model):
        with autotest.step("Assert level at 5 attempts"):
            agent = HintAgent(config_model)
            assert_equal(agent.tools.get_hint_level(5), 3, "level 3")
            assert_equal(agent.tools.get_remaining_hints(3), 0, "no hints remaining")
