import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_false,
    assert_greater_equal,
    assert_true,
)

from config.config_model import LearningAnalyticsConfig
from evaluation.harness import run_identifier
from evaluation.scenarios import make_normal_scenario, make_struggle_scenario
from learning_analytics.process_state import ProcessRegime

pytestmark = [pytest.mark.unit]


class TestHarness:
    @autotest.num("1660")
    @autotest.external_id("a3f7c21e-4b58-4d09-9e6a-1c2d3e4f5a6b")
    @autotest.name("harness: струггл детектится после онсета при T_k=0")
    def test_a3f7c21e_detects_struggle(self):
        with autotest.step("Arrange: repeating_errors онсет на 90с"):
            s = make_struggle_scenario(
                ProcessRegime.REPEATING_ERRORS, onset_index=6, n=12, step=15.0
            )
            cfg = LearningAnalyticsConfig()
        with autotest.step("Act: T_k=0 (мгновенно)"):
            d = run_identifier(s, t_k=0.0, config=cfg)
        with autotest.step("Assert: детект, ts>=онсет, тип repeating"):
            assert_true(d.detected, "детект")
            assert_greater_equal(d.detected_ts, 90.0, "не раньше онсета")
            assert_equal(d.detected_regime, ProcessRegime.REPEATING_ERRORS, "тип")

    @autotest.num("1661")
    @autotest.external_id("b4e8d32f-5c69-4e1a-af7b-2d3e4f5a6b7c")
    @autotest.name("harness: нормальная сессия не даёт детекта")
    def test_b4e8d32f_normal_no_detect(self):
        with autotest.step("Act"):
            d = run_identifier(
                make_normal_scenario(n=12), t_k=0.0, config=LearningAnalyticsConfig()
            )
        with autotest.step("Assert: нет детекта"):
            assert_false(d.detected, "нет ложного")

    @autotest.num("1662")
    @autotest.external_id("c5f9e43a-6d7a-4f2b-b08c-3e4f5a6b7c8d")
    @autotest.name("harness: больший T_k откладывает детект")
    def test_c5f9e43a_higher_tk_delays(self):
        with autotest.step("Arrange"):
            s = make_struggle_scenario(ProcessRegime.STUCK_ON_STEP, onset_index=4, n=12, step=15.0)
            cfg = LearningAnalyticsConfig()
        with autotest.step("Act: T_k=0 vs T_k=30"):
            d0 = run_identifier(s, 0.0, cfg)
            d30 = run_identifier(s, 30.0, cfg)
        with autotest.step("Assert: при T_k=30 детект позже (или нет), чем при 0"):
            assert_true(d0.detected, "T_k=0 детект")
            if d30.detected:
                assert_greater_equal(d30.detected_ts, d0.detected_ts, "позже")
