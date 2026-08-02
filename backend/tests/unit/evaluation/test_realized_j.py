"""Test: J is charged against identifier output, not against ground-truth labels."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from config.config_model import LearningAnalyticsConfig
from control.criterion import Costs, compute_J
from control.derive_thresholds import total_J
from evaluation.metrics import j_optimal, operating_curve
from evaluation.scenarios import make_normal_scenario, make_struggle_scenario
from learning_analytics.process_state import ProcessRegime

pytestmark = [pytest.mark.unit]

_GRID = [0.0, 15.0, 30.0, 60.0, 90.0, 120.0]
_SESSION_SECONDS = 14 * 15.0


def _delayed_scenarios():
    """Struggle sessions detected late, plus one clean normal session."""
    scns = [
        make_struggle_scenario(
            ProcessRegime.REPEATING_ERRORS,
            onset_index=4,
            n=14,
            step=15.0,
            window=_SESSION_SECONDS,
            detect_delay=delay,
        )
        for delay in (0, 2, 4)
    ]
    scns.append(make_normal_scenario(n=14, step=15.0))
    return scns


class TestRealizedJ:
    @autotest.num("3001")
    @autotest.external_id("50d70c9a-7492-4427-9eb8-bcafe43945fb")
    @autotest.name("total_J: firing comes from detections, cost is charged against truth")
    def test_50d70c9a_detections_drive_firing_not_truth(self):
        with autotest.step("Arrange: truth is in a bad regime, the detector does not see it"):
            truth = [
                {"ts": 0.0, "regime": "stuck_on_step", "dwell": 0.0},
                {"ts": 30.0, "regime": "stuck_on_step", "dwell": 30.0},
                {"ts": 60.0, "regime": "productive", "dwell": 0.0},
            ]
            blind = [
                {"ts": 0.0, "regime": "productive", "dwell": 0.0},
                {"ts": 30.0, "regime": "productive", "dwell": 30.0},
                {"ts": 60.0, "regime": "productive", "dwell": 60.0},
            ]
            costs = Costs(c_stuck=1.0, c_intervention=1.0, c_false=1.0)
            thresholds = {"stuck_on_step": 0.0}

        with autotest.step("Act: compute J with and without detections"):
            j_oracle = total_J([{"samples": truth}], costs, thresholds)
            j_realized = total_J([{"samples": truth, "detections": blind}], costs, thresholds)

        with autotest.step("Assert: the blind detector costs more than the oracle, never fires"):
            assert_true(j_realized > j_oracle, f"J realized {j_realized} <= oracle {j_oracle}")
            assert_equal(j_realized, 60.0, "J == bad_duration with no interventions")

    @autotest.num("3002")
    @autotest.external_id("12d43428-6c01-4d00-a50c-10c2c41dafcd")
    @autotest.name("compute_J: an intervention outside a bad regime counts as false")
    def test_12d43428_intervention_on_productive_is_false(self):
        with autotest.step("Arrange: productive session and one intervention"):
            samples = [
                {"ts": 0.0, "regime": "productive", "dwell": 0.0},
                {"ts": 30.0, "regime": "productive", "dwell": 30.0},
                {"ts": 60.0, "regime": "productive", "dwell": 60.0},
            ]
            costs = Costs(c_stuck=1.0, c_intervention=1.0, c_false=10.0)

        with autotest.step("Act: compute_J"):
            res = compute_J(samples, [{"ts": 30.0}], costs)

        with autotest.step("Assert: n_false == 1, the penalty lands in J"):
            assert_equal(res.n_false, 1, f"n_false == {res.n_false}")
            assert_equal(res.bad_duration, 0.0, "bad_duration == 0")
            assert_equal(res.J, 11.0, "J == c_intervention + c_false")

    @autotest.num("3003")
    @autotest.external_id("29b55dae-0687-4a09-ac6d-e8f5f9b36338")
    @autotest.name("operating_curve: J responds to c_false")
    def test_29b55dae_curve_responds_to_false_cost(self):
        with autotest.step("Arrange: normal session with detector blips"):
            scns = [
                make_struggle_scenario(
                    ProcessRegime.REPEATING_ERRORS,
                    onset_index=4,
                    n=14,
                    step=15.0,
                    window=_SESSION_SECONDS,
                ),
                make_normal_scenario(n=14, step=15.0, blip_indices=(3, 4)),
            ]
            cfg = LearningAnalyticsConfig()

        with autotest.step("Act: curves for a cheap and an expensive false intervention"):
            cheap = operating_curve(scns, _GRID, cfg, Costs(1.0, 1.0, 1.0))
            pricey = operating_curve(scns, _GRID, cfg, Costs(1.0, 1.0, 500.0))

        with autotest.step("Assert: an expensive false alarm raises J at a small T_k"):
            assert_true(pricey[0].J > cheap[0].J, f"J {pricey[0].J} <= {cheap[0].J}")

    @autotest.num("3004")
    @autotest.external_id("748a4589-607b-4fa2-b51c-a23375cc384b")
    @autotest.name("operating_curve: recall degrades across the T_k grid, is not identically 1.0")
    def test_748a4589_recall_degrades_across_grid(self):
        with autotest.step("Arrange: scenarios with detection delay"):
            scns = _delayed_scenarios()

        with autotest.step("Act: build the operating curve"):
            curve = operating_curve(scns, _GRID, LearningAnalyticsConfig(), Costs(1.0, 1.0, 1.0))

        with autotest.step("Assert: recall is not constant, decreases, optimum lies on the grid"):
            recalls = [p.recall for p in curve]
            assert_true(len(set(recalls)) > 1, f"recall is constant: {recalls}")
            assert_true(recalls[-1] < recalls[0], f"recall does not decrease: {recalls}")
            assert_true(j_optimal(curve).t_k in _GRID, "optimum is off-grid")
