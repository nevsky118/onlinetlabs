import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents._shared import format_failing_check
from agents.base import BaseAgent
from agents.hint.models import HintInput
from agents.tutor.models import TutorInput
from i18n import DEFAULT_LOCALE
from learning_analytics.context import AgentContext

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class _Dummy(BaseAgent):
    def system_prompt(self, locale):
        return f"sp-{locale}"


def _context() -> AgentContext:
    return AgentContext(
        topology_summary="2 nodes",
        recent_errors=["timeout"],
        recent_actions=["start PC1"],
        struggle_type="stuck_on_step",
        dominant_error="timeout",
        features_summary="12 events",
    )


class TestAgentLocale:
    @autotest.num("3123")
    @autotest.external_id("ffd6c1cc-59b2-46af-aeec-b6f95d8f2be0")
    @autotest.name("BaseAgent: _agent_for passes the locale to system_prompt")
    def test_ffd6c1cc_agent_for_uses_locale(self, config_model):
        with autotest.step("Arrange: a dummy agent over the shared config"):
            agent = _Dummy(config_model)

        with autotest.step("Act: build agents for both locales"):
            en = agent._agent_for("yandex-gpt-5.1", "en")
            ru = agent._agent_for("yandex-gpt-5.1", "ru")

        with autotest.step("Assert: each pydantic-ai Agent carries its locale's prompt"):
            assert_true(en is not ru, "_agent_for still builds a fresh Agent per call")
            assert_equal(agent.system_prompt("ru"), "sp-ru", "system_prompt receives the locale")

    @autotest.num("3124")
    @autotest.external_id("4ae1ccc2-51b0-4a76-8104-82ae79fbd67b")
    @autotest.name("agent inputs: locale defaults to the default locale")
    def test_4ae1ccc2_input_locale_default(self):
        with autotest.step("Act: build inputs without an explicit locale"):
            tutor = TutorInput(session_id="s1", user_id="u1", question="why")
            hint = HintInput(
                session_id="s1", user_id="u1", lab_slug="lab", step_slug="step-1", attempts_count=0
            )

        with autotest.step("Assert: both default rather than requiring every caller to pass one"):
            assert_equal(tutor.locale, DEFAULT_LOCALE, "TutorInput.locale defaults")
            assert_equal(hint.locale, DEFAULT_LOCALE, "HintInput.locale defaults")

    @autotest.num("3125")
    @autotest.external_id("bad1daff-4c5e-4253-b6c4-019fd6770fff")
    @autotest.name("format_failing_check: renders per locale and keeps the check kind verbatim")
    def test_bad1daff_failing_check_localised(self):
        with autotest.step("Arrange: a failed vpcs.show_ip check on PC1"):
            check = {
                "kind": "vpcs.show_ip",
                "params": {"node": "PC1"},
                "expected": "192.168.1.11/24",
                "actual": "none",
            }

        with autotest.step("Act: format the same failed check in both locales"):
            en = format_failing_check(check, "en")
            ru = format_failing_check(check, "ru")

        with autotest.step("Assert: prose differs, identifiers do not"):
            assert_true(en != ru, "the sentence is translated")
            for rendered in (en, ru):
                assert_true("vpcs.show_ip" in rendered, "the check kind stays verbatim")
                assert_true("PC1" in rendered, "the node name stays verbatim")

    @autotest.num("3126")
    @autotest.external_id("ef8645bd-62c9-455c-ae65-4bf66ea45295")
    @autotest.name("format_failing_check: a check without a node omits the node clause")
    def test_ef8645bd_failing_check_without_node(self):
        with autotest.step("Act: format a check that carries no node"):
            rendered = format_failing_check(
                {"kind": "vpcs.ping", "params": None, "expected": "ok", "actual": "loss"}, "en"
            )

        with autotest.step("Assert: no dangling separator is left behind"):
            assert_true("None" not in rendered, "an absent node is omitted, not stringified")

    @autotest.num("3127")
    @autotest.external_id("dc098088-7545-4d47-b03a-3351b1991bf5")
    @autotest.name("AgentContext.to_prompt: header and labels follow the locale")
    def test_dc098088_context_localised(self):
        with autotest.step("Act: render the same context in both locales"):
            en = _context().to_prompt("en")
            ru = _context().to_prompt("ru")

        with autotest.step("Assert: prose differs, data survives in both"):
            assert_true(en != ru, "labels are translated")
            for rendered in (en, ru):
                assert_true("2 nodes" in rendered, "topology data survives")
                assert_true("timeout" in rendered, "error data survives")
