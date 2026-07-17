import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_less_equal, assert_true

from control.criterion import Costs
from control.derive_thresholds import derive_T_k, sensitivity_curve, simulate_interventions

pytestmark = [pytest.mark.unit]


def _session(spell_len, regime="stuck_on_step"):
    # один плохой спелл длиной spell_len (шаг 15с), затем продуктивный
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
    @autotest.name("simulate_interventions: cooldown=9999 → ровно одна интервенция на спелл")
    def test_5b3f4ce7_simulate_one_per_spell(self):
        with autotest.step("Arrange: сессия 60с, cooldown=9999"):
            s = _session(60)

        with autotest.step("Act: simulate_interventions с порогом 30, cooldown=9999"):
            ivs = simulate_interventions(
                s["samples"], {"stuck_on_step": 30.0}, cooldown_seconds=9999
            )

        with autotest.step("Assert: ровно одна интервенция"):
            assert_equal(len(ivs), 1, "cooldown=9999 → один выстрел на спелл")

    @autotest.num("1453")
    @autotest.external_id("9c4cf685-6796-4861-b101-0b26f6b4be6c")
    @autotest.name("simulate_interventions: cooldown=0 → выстрел на каждый сэмпл >= порога")
    def test_9c4cf685_simulate_cooldown_gates(self):
        with autotest.step("Arrange: сессия 60с, cooldown=0"):
            s = _session(60)

        with autotest.step("Act: simulate_interventions с порогом 30, cooldown=0"):
            ivs = simulate_interventions(
                s["samples"], {"stuck_on_step": 30.0}, cooldown_seconds=0.0
            )

        with autotest.step("Assert: три интервенции (dwell=30,45,60)"):
            assert_equal(len(ivs), 3, "cooldown=0 → 3 выстрела (dwell 30,45,60)")

    @autotest.num("1454")
    @autotest.external_id("7bcdf15e-b770-4b17-ae22-9626bd9dfb99")
    @autotest.name("simulate_interventions: дефолтный cooldown=0 совпадает с явным cooldown=0")
    def test_7bcdf15e_simulate_default_cooldown_zero(self):
        with autotest.step("Arrange: сессия 60с"):
            s = _session(60)

        with autotest.step("Act: explicit cooldown=0 и дефолт"):
            ivs_explicit = simulate_interventions(
                s["samples"], {"stuck_on_step": 30.0}, cooldown_seconds=0.0
            )
            ivs_default = simulate_interventions(s["samples"], {"stuck_on_step": 30.0})

        with autotest.step("Assert: количество интервенций совпадает"):
            assert_equal(len(ivs_explicit), len(ivs_default), "дефолт == cooldown=0")

    @autotest.num("1455")
    @autotest.external_id("cb59ed3e-ea4c-475d-bbbc-dc04984b11d6")
    @autotest.name("derive_T_k: дорогое застревание → T_k ниже или равен дешёвому")
    def test_cb59ed3e_derive_picks_min_J(self):
        with autotest.step("Arrange: три сессии, сетка порогов"):
            sessions = [_session(30), _session(30), _session(120)]
            grid = {"stuck_on_step": [0, 15, 30, 45, 60]}
            costs_high_stuck = Costs(c_stuck=5.0 / 60, c_intervention=1.0, c_false=0.0)
            costs_low_stuck = Costs(c_stuck=0.1 / 60, c_intervention=1.0, c_false=0.0)

        with autotest.step("Act: derive_T_k для обеих стоимостей"):
            tk_high = derive_T_k(sessions, costs_high_stuck, grid)
            tk_low = derive_T_k(sessions, costs_low_stuck, grid)

        with autotest.step("Assert: дороже застревание → T_k <= T_k при дешёвом"):
            assert_less_equal(
                tk_high["stuck_on_step"],
                tk_low["stuck_on_step"],
                "дорогое застревание → не выше T_k",
            )

    @autotest.num("1456")
    @autotest.external_id("795eca61-5cee-4bfe-b4a4-06ce8650c25d")
    @autotest.name("sensitivity_curve: кривая T_k монотонно убывает с ростом стоимости застревания")
    def test_795eca61_sensitivity_monotone(self):
        with autotest.step("Arrange: две сессии, ratios=[0.2,1.0,5.0]"):
            sessions = [_session(30), _session(120)]

        with autotest.step("Act: sensitivity_curve"):
            curve = sensitivity_curve(
                sessions,
                ratios=[0.2, 1.0, 5.0],
                grid={"stuck_on_step": [0, 15, 30, 45, 60]},
            )

        with autotest.step("Assert: T_k не возрастает (убывает или стабилен)"):
            tks = [pt[1]["stuck_on_step"] for pt in curve]
            assert_true(
                tks == sorted(tks, reverse=True),
                "дороже застревание → T_k не возрастает",
            )
