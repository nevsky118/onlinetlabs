import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true

from evaluation.scenarios import is_normal, make_normal_scenario, make_struggle_scenario
from learning_analytics.process_state import ProcessRegime

pytestmark = [pytest.mark.unit]


class TestScenarios:
    @autotest.num("1650")
    @autotest.external_id("6acd66d7-813b-4f10-8cb9-3baf64db6c17")
    @autotest.name("scenarios: normal scenario without onset")
    def test_6acd66d7_normal(self):
        with autotest.step("Act"):
            s = make_normal_scenario(n=10)
        with autotest.step("Assert: productive, no onset, 10 snapshots"):
            assert_true(is_normal(s), "normal")
            assert_is_none(s.onset_ts, "no onset")
            assert_equal(len(s.snapshots), 10, "snapshots")

    @autotest.num("1651")
    @autotest.external_id("81bd2b96-08a5-4b54-8a83-b78b866a2326")
    @autotest.name("scenarios: struggle scenario with onset and type")
    def test_81bd2b96_struggle(self):
        with autotest.step("Act: repeating_errors at index 6"):
            s = make_struggle_scenario(
                ProcessRegime.REPEATING_ERRORS, onset_index=6, n=12, step=15.0
            )
        with autotest.step("Assert: type, onset=6*15, features trip after onset"):
            assert_equal(s.truth_regime, ProcessRegime.REPEATING_ERRORS, "type")
            assert_equal(s.onset_ts, 90.0, "onset ts")
            assert_true(
                s.snapshots[7].features.error_repeat_count >= 5, "feature tripped after onset"
            )
            assert_equal(s.snapshots[0].features.error_repeat_count, 0, "benign before onset")
