import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_less_equal, assert_true

from control.criterion import Costs
from control.derive_thresholds import derive_T_k, sensitivity_curve, simulate_interventions

pytestmark = [pytest.mark.unit]


def _session(spell_len, regime="stuck_on_step"):
    # one bad spell of length spell_len (15s step), then productive
    samples, t = [], 0
    dwell = 0.0
    while t <= spell_len:
        samples.append({"ts": t, "regime": regime, "dwell": dwell})
        t += 15
        dwell += 15.0
    samples.append({"ts": t, "regime": "productive", "dwell": 0.0})
    return {"samples": samples, "interventions": []}


class TestDeriveThresholds:
    @autotest.num("1452")
    @autotest.external_id("5b3f4ce7-a03a-4308-9104-c0a340dab65e")
    @autotest.name("simulate_interventions: cooldown=9999 → exactly one intervention per spell")
    def test_5b3f4ce7_simulate_one_per_spell(self):
        with autotest.step("Arrange: 60s session, cooldown=9999"):
            s = _session(60)

        with autotest.step("Act: simulate_interventions with threshold 30, cooldown=9999"):
            ivs = simulate_interventions(
                s["samples"], {"stuck_on_step": 30.0}, cooldown_seconds=9999
            )

        with autotest.step("Assert: exactly one intervention"):
            assert_equal(len(ivs), 1, "cooldown=9999 → one shot per spell")

    @autotest.num("1453")
    @autotest.external_id("9c4cf685-6796-4861-b101-0b26f6b4be6c")
    @autotest.name("simulate_interventions: cooldown=0 → shot on every sample >= threshold")
    def test_9c4cf685_simulate_cooldown_gates(self):
        with autotest.step("Arrange: 60s session, cooldown=0"):
            s = _session(60)

        with autotest.step("Act: simulate_interventions with threshold 30, cooldown=0"):
            ivs = simulate_interventions(
                s["samples"], {"stuck_on_step": 30.0}, cooldown_seconds=0.0
            )

        with autotest.step("Assert: three interventions (dwell=30,45,60)"):
            assert_equal(len(ivs), 3, "cooldown=0 → 3 shots (dwell 30,45,60)")

    @autotest.num("1454")
    @autotest.external_id("7bcdf15e-b770-4b17-ae22-9626bd9dfb99")
    @autotest.name("simulate_interventions: default cooldown=0 matches explicit cooldown=0")
    def test_7bcdf15e_simulate_default_cooldown_zero(self):
        with autotest.step("Arrange: 60s session"):
            s = _session(60)

        with autotest.step("Act: explicit cooldown=0 and default"):
            ivs_explicit = simulate_interventions(
                s["samples"], {"stuck_on_step": 30.0}, cooldown_seconds=0.0
            )
            ivs_default = simulate_interventions(s["samples"], {"stuck_on_step": 30.0})

        with autotest.step("Assert: intervention count matches"):
            assert_equal(len(ivs_explicit), len(ivs_default), "default == cooldown=0")

    @autotest.num("1455")
    @autotest.external_id("cb59ed3e-ea4c-475d-bbbc-dc04984b11d6")
    @autotest.name("derive_T_k: expensive stuck-time → T_k at or below the cheap case")
    def test_cb59ed3e_derive_picks_min_J(self):
        with autotest.step("Arrange: three sessions, threshold grid"):
            sessions = [_session(30), _session(30), _session(120)]
            grid = {"stuck_on_step": [0, 15, 30, 45, 60]}
            costs_high_stuck = Costs(c_stuck=5.0 / 60, c_intervention=1.0, c_false=0.0)
            costs_low_stuck = Costs(c_stuck=0.1 / 60, c_intervention=1.0, c_false=0.0)

        with autotest.step("Act: derive_T_k for both cost sets"):
            tk_high = derive_T_k(sessions, costs_high_stuck, grid)
            tk_low = derive_T_k(sessions, costs_low_stuck, grid)

        with autotest.step("Assert: pricier stuck-time → T_k <= T_k at cheaper cost"):
            assert_less_equal(
                tk_high["stuck_on_step"],
                tk_low["stuck_on_step"],
                "expensive stuck-time → T_k not higher",
            )

    @autotest.num("1456")
    @autotest.external_id("795eca61-5cee-4bfe-b4a4-06ce8650c25d")
    @autotest.name("sensitivity_curve: T_k curve decreases monotonically as stuck cost grows")
    def test_795eca61_sensitivity_monotone(self):
        with autotest.step("Arrange: two sessions, ratios=[0.2,1.0,5.0]"):
            sessions = [_session(30), _session(120)]

        with autotest.step("Act: sensitivity_curve"):
            curve = sensitivity_curve(
                sessions,
                ratios=[0.2, 1.0, 5.0],
                grid={"stuck_on_step": [0, 15, 30, 45, 60]},
            )

        with autotest.step("Assert: T_k does not increase (decreasing or flat)"):
            tks = [pt[1]["stuck_on_step"] for pt in curve]
            assert_true(
                tks == sorted(tks, reverse=True),
                "pricier stuck-time → T_k does not increase",
            )
