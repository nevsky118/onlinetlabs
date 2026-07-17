import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true

from evaluation.scenarios import is_normal, make_normal_scenario, make_struggle_scenario
from learning_analytics.process_state import ProcessRegime

pytestmark = [pytest.mark.unit]


class TestScenarios:
    @autotest.num("1650")
    @autotest.external_id("6acd66d7-813b-4f10-8cb9-3baf64db6c17")
    @autotest.name("scenarios: нормальный сценарий без онсета")
    def test_6acd66d7_normal(self):
        with autotest.step("Act"):
            s = make_normal_scenario(n=10)
        with autotest.step("Assert: productive, без онсета, 10 снапшотов"):
            assert_true(is_normal(s), "нормальный")
            assert_is_none(s.onset_ts, "нет онсета")
            assert_equal(len(s.snapshots), 10, "снапшоты")

    @autotest.num("1651")
    @autotest.external_id("81bd2b96-08a5-4b54-8a83-b78b866a2326")
    @autotest.name("scenarios: струггл-сценарий с онсетом и типом")
    def test_81bd2b96_struggle(self):
        with autotest.step("Act: repeating_errors на индексе 6"):
            s = make_struggle_scenario(
                ProcessRegime.REPEATING_ERRORS, onset_index=6, n=12, step=15.0
            )
        with autotest.step("Assert: тип, онсет=6*15, фичи пробивают после онсета"):
            assert_equal(s.truth_regime, ProcessRegime.REPEATING_ERRORS, "тип")
            assert_equal(s.onset_ts, 90.0, "онсет ts")
            assert_true(
                s.snapshots[7].features.error_repeat_count >= 5, "фича пробита после онсета"
            )
            assert_equal(s.snapshots[0].features.error_repeat_count, 0, "до онсета benign")
