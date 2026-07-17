from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_false, assert_true

from agents.analytics.models import StruggleType
from learning_analytics.process_state import ProcessRegime, analysis_to_regime, is_bad

pytestmark = [pytest.mark.unit]


class TestProcessState:
    @autotest.num("1572")
    @autotest.external_id("e1f4efe4-7bbc-4b12-b7b6-9175cc3ab8f1")
    @autotest.name("ProcessState: нет борьбы → PRODUCTIVE, is_bad=False")
    def test_e1f4efe4_productive_when_no_struggle(self):
        with autotest.step("Arrange: анализ без борьбы"):
            a = SimpleNamespace(struggle_detected=False, struggle_type=None)

        with autotest.step("Act: определить режим и is_bad"):
            regime = analysis_to_regime(a)
            bad = is_bad(ProcessRegime.PRODUCTIVE)

        with autotest.step("Assert: режим PRODUCTIVE, is_bad=False"):
            assert_equal(regime, ProcessRegime.PRODUCTIVE, "режим — PRODUCTIVE")
            assert_false(bad, "PRODUCTIVE не является плохим режимом")

    @autotest.num("1573")
    @autotest.external_id("a08292ae-4579-43d2-8d94-e3713a4fb2b1")
    @autotest.name("ProcessState: борьба STUCK_ON_STEP → режим STUCK_ON_STEP, is_bad=True")
    def test_a08292ae_regime_mirrors_struggle_type(self):
        with autotest.step("Arrange: анализ с борьбой STUCK_ON_STEP"):
            a = SimpleNamespace(struggle_detected=True, struggle_type=StruggleType.STUCK_ON_STEP)

        with autotest.step("Act: определить режим"):
            r = analysis_to_regime(a)

        with autotest.step("Assert: режим STUCK_ON_STEP, value=stuck_on_step, is_bad=True"):
            assert_equal(r, ProcessRegime.STUCK_ON_STEP, "режим — STUCK_ON_STEP")
            assert_equal(r.value, "stuck_on_step", "value enum — stuck_on_step")
            assert_true(is_bad(r), "STUCK_ON_STEP является плохим режимом")
