import pytest
from control.derive_thresholds import derive_T_k, sensitivity_curve, simulate_interventions
from control.criterion import Costs

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


def test_simulate_one_per_spell():
    # cooldown=9999 → второй выстрел заблокирован, ровно один на спелл
    s = _session(60)  # dwell растёт 0,15,30,45,60
    ivs = simulate_interventions(s["samples"], {"stuck_on_step": 30.0}, cooldown_seconds=9999)
    assert len(ivs) == 1


def test_simulate_cooldown_gates():
    # cooldown=0 → выстрел на каждый сэмпл с dwell>=30 (при 30,45,60 = 3 выстрела)
    s = _session(60)
    ivs = simulate_interventions(s["samples"], {"stuck_on_step": 30.0}, cooldown_seconds=0.0)
    # dwell=30 (t=30), dwell=45 (t=45), dwell=60 (t=60) — три сэмпла проходят порог
    assert len(ivs) == 3


def test_simulate_default_cooldown_zero():
    # cooldown по умолчанию = 0.0 → поведение совпадает с cooldown=0
    s = _session(60)
    ivs_explicit = simulate_interventions(s["samples"], {"stuck_on_step": 30.0}, cooldown_seconds=0.0)
    ivs_default = simulate_interventions(s["samples"], {"stuck_on_step": 30.0})
    assert len(ivs_explicit) == len(ivs_default)


def test_derive_picks_min_J():
    # Оптимизатор должен выбрать T_k с минимальным J по сетке.
    # Высокий c_stuck/c_int → интервенции дешевле застревания → ниже T_k.
    # c_stuck в «мин⁻¹»: при c_stuck/60=1/60, c_int=1 → D*=60с; длинный спелл 120с > 60с → огонь.
    sessions = [_session(30), _session(30), _session(120)]
    grid = {"stuck_on_step": [0, 15, 30, 45, 60]}
    costs_high_stuck = Costs(c_stuck=5.0 / 60, c_intervention=1.0, c_false=0.0)
    tk_high = derive_T_k(sessions, costs_high_stuck, grid)
    costs_low_stuck = Costs(c_stuck=0.1 / 60, c_intervention=1.0, c_false=0.0)
    tk_low = derive_T_k(sessions, costs_low_stuck, grid)
    # дороже застревание → меньше или равно T_k (не выше)
    assert tk_high["stuck_on_step"] <= tk_low["stuck_on_step"]


def test_sensitivity_monotone():
    sessions = [_session(30), _session(120)]
    curve = sensitivity_curve(
        sessions,
        ratios=[0.2, 1.0, 5.0],
        grid={"stuck_on_step": [0, 15, 30, 45, 60]},
    )
    tks = [pt[1]["stuck_on_step"] for pt in curve]
    assert tks == sorted(tks, reverse=True)  # дороже застревание → ниже порог (не возрастает)
