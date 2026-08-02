import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from evaluation.harness import Detection
from evaluation.metrics import confusion_matrix
from evaluation.scenarios import make_struggle_scenario
from learning_analytics.process_state import ProcessRegime

pytestmark = [pytest.mark.unit]


class TestConfusion:
    @autotest.num("1680")
    @autotest.external_id("fb8c9b70-a34c-49f0-91e7-abc74e75b8c5")
    @autotest.name("confusion: correct type on diagonal, type error off diagonal")
    def test_fb8c9b70_matrix(self):
        with autotest.step(
            "Arrange: repeating detected as repeating; stuck detected as idle (type error)"
        ):
            s1 = make_struggle_scenario(ProcessRegime.REPEATING_ERRORS, onset_index=4)
            s2 = make_struggle_scenario(ProcessRegime.STUCK_ON_STEP, onset_index=4)
            pairs = [
                (s1, Detection(True, 75.0, ProcessRegime.REPEATING_ERRORS)),
                (s2, Detection(True, 75.0, ProcessRegime.IDLE)),
            ]
        with autotest.step("Act"):
            cm = confusion_matrix(pairs)
        with autotest.step("Assert: diagonal repeating=1, stuck→idle=1"):
            assert_equal(
                cm[ProcessRegime.REPEATING_ERRORS][ProcessRegime.REPEATING_ERRORS],
                1,
                "correct type",
            )
            assert_equal(cm[ProcessRegime.STUCK_ON_STEP][ProcessRegime.IDLE], 1, "type error")

    @autotest.num("1681")
    @autotest.external_id("9fc90dc3-521b-4d28-a124-8d859f0f8646")
    @autotest.name("confusion: no detection → PRODUCTIVE column")
    def test_9fc90dc3_no_detect(self):
        with autotest.step("Arrange: idle not detected"):
            s = make_struggle_scenario(ProcessRegime.IDLE, onset_index=4)
            pairs = [(s, Detection(False, None, None))]
        with autotest.step("Act"):
            cm = confusion_matrix(pairs)
        with autotest.step("Assert: idle row, PRODUCTIVE column = 1"):
            assert_equal(cm[ProcessRegime.IDLE][ProcessRegime.PRODUCTIVE], 1, "miss → PRODUCTIVE")
