"""Test: the intervention gates, in the order the control law fixes them."""

from datetime import UTC, datetime, timedelta

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from analytics.runtime.control_law import should_intervene
from analytics.runtime.process_state import ProcessRegime
from config.config_model import LearningAnalyticsConfig
from experiment.assignment import ControlArm

pytestmark = [pytest.mark.unit]

_NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _cfg(**overrides) -> LearningAnalyticsConfig:
    defaults = dict(
        dwell_thresholds={"stuck_on_step": 60.0},
        cooldown_period=60.0,
        mrt_hold_probability=0.5,
    )
    return LearningAnalyticsConfig(**(defaults | overrides))


def _decide(**overrides):
    args = dict(
        regime=ProcessRegime.STUCK_ON_STEP,
        dwell=120.0,
        arm=ControlArm.CLOSED,
        last_intervention_at=None,
        cfg=_cfg(),
        now=_NOW,
    )
    return should_intervene(**(args | overrides))


class TestControlLaw:
    @autotest.num("3021")
    @autotest.external_id("ccaccba3-a91b-46d7-8c7a-83c1bc587555")
    @autotest.name("should_intervene: closed arm past the threshold intervenes")
    def test_ccaccba3_closed_arm_intervenes(self):
        with autotest.step("Act: closed arm, dwell over T_k, no cooldown"):
            decision = _decide()

        with autotest.step("Assert: intervene"):
            assert_equal(decision.action, "intervene", decision.reason)
            assert_equal(decision.reason, "threshold_reached", "reason")

    @autotest.num("3022")
    @autotest.external_id("15c51420-1b55-45a2-bd77-bfd16275fb59")
    @autotest.name("should_intervene: productive regime is not a decision point")
    def test_15c51420_productive_skips(self):
        with autotest.step("Act: productive regime"):
            decision = _decide(regime=ProcessRegime.PRODUCTIVE)

        with autotest.step("Assert: skip"):
            assert_equal(decision.action, "skip", decision.reason)
            assert_equal(decision.reason, "productive", "reason")

    @autotest.num("3023")
    @autotest.external_id("bb8bc962-86df-47cd-97ab-7944471edb65")
    @autotest.name("should_intervene: dwell below T_k skips")
    def test_bb8bc962_below_threshold_skips(self):
        with autotest.step("Act: dwell under the configured T_k"):
            decision = _decide(dwell=30.0)

        with autotest.step("Assert: skip"):
            assert_equal(decision.action, "skip", decision.reason)
            assert_equal(decision.reason, "dwell_below_threshold", "reason")

    @autotest.num("3024")
    @autotest.external_id("85b56a73-8ee8-4632-8e15-9d301ca6a017")
    @autotest.name("should_intervene: cooldown not elapsed skips")
    def test_85b56a73_cooldown_skips(self):
        with autotest.step("Act: last intervention 10s ago, cooldown 60s"):
            decision = _decide(last_intervention_at=_NOW - timedelta(seconds=10))

        with autotest.step("Assert: skip"):
            assert_equal(decision.action, "skip", decision.reason)
            assert_equal(decision.reason, "cooldown", "reason")

    @autotest.num("3025")
    @autotest.external_id("f0e9b1a8-7914-4620-9003-335450c4c695")
    @autotest.name("should_intervene: open arm withholds even when MRT draws intervene")
    def test_f0e9b1a8_open_arm_beats_mrt_draw(self):
        with autotest.step("Act: open arm, MRT draw that would mean intervene"):
            decision = _decide(arm=ControlArm.OPEN, mrt_threshold=60.0, hold_draw=0.99)

        with autotest.step("Assert: withhold on the arm, not on the draw"):
            assert_equal(decision.action, "withhold", decision.reason)
            assert_equal(decision.reason, "open_arm", "the arm gate precedes the MRT draw")

    @autotest.num("3026")
    @autotest.external_id("0af3e8b2-032b-4233-9ff4-32a45420d299")
    @autotest.name("should_intervene: MRT uses the spell threshold and its own draw")
    def test_0af3e8b2_mrt_threshold_and_draw(self):
        with autotest.step("Act: dwell under the jittered spell T_k"):
            below = _decide(dwell=70.0, mrt_threshold=90.0, hold_draw=0.99)

        with autotest.step("Assert: the spell threshold wins over the configured one"):
            assert_equal(below.action, "skip", below.reason)
            assert_equal(below.reason, "dwell_below_threshold", "reason")

        with autotest.step("Act: past the spell T_k, draw below the hold probability"):
            held = _decide(dwell=120.0, mrt_threshold=90.0, hold_draw=0.1)

        with autotest.step("Assert: withheld by the randomizer"):
            assert_equal(held.action, "withhold", held.reason)
            assert_equal(held.reason, "mrt_hold", "reason")
