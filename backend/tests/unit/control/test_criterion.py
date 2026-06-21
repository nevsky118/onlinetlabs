import pytest
from control.criterion import compute_J, Costs
pytestmark = [pytest.mark.unit]


def test_J_sums_duration_and_interventions():
    # bad_duration = 2×30 = 60; один спелл с интервенцией, clean-выходов нет → n_false=0
    samples = [
        {"ts": 0, "regime": "stuck_on_step", "dwell": 0},
        {"ts": 30, "regime": "stuck_on_step", "dwell": 30},
        {"ts": 60, "regime": "productive", "dwell": 0},
    ]
    interventions = [{"ts": 45}]
    costs = Costs(c_stuck=1.0, c_intervention=2.0, c_false=0.5)
    res = compute_J(samples, interventions, costs, dwell_thresholds={"stuck_on_step": 0.0})
    assert res.bad_duration == 60.0
    assert res.n_interventions == 1
    assert res.n_false == 0          # нет clean-выходов → ложных не засчитываем
    assert res.J == 60.0 * 1.0 + 1 * 2.0 + 0 * 0.5  # == 62.0


def test_no_interventions_zero_false():
    samples = [{"ts": 0, "regime": "productive", "dwell": 0}]
    res = compute_J(samples, [], Costs(1.0, 1.0, 1.0))
    assert res.J == 0.0 and res.n_interventions == 0 and res.n_false == 0


def test_count_false_flags_premature_intervention():
    """Ложное вмешательство засчитывается, когда спелл с интервенцией
    завершился быстрее медианного чистого самовыхода.

    Данные: три спелла без интервенции (самовыход за 60с каждый) → median=60;
    один спелл с интервенцией, завершившийся за 20с → n_false==1.
    """
    # Три clean-спелла (самовыход за 60с), шаг 10с
    def _spell(start: int, duration: int, with_iv: bool) -> list[dict]:
        """Возвращает сэмплы одного спелла [start, start+duration]."""
        result = []
        t = start
        while t < start + duration:
            result.append({"ts": t, "regime": "stuck_on_step", "dwell": float(t - start)})
            t += 10
        # выход в продуктивный режим
        result.append({"ts": t, "regime": "productive", "dwell": 0.0})
        return result

    # Три clean-спелла: t=0..60, t=70..130, t=140..200 (duration=60 каждый)
    samples = (
        _spell(0, 60, with_iv=False)
        + _spell(70, 60, with_iv=False)
        + _spell(140, 60, with_iv=False)
        # спелл с интервенцией: t=210..230 (duration=20 < median=60) → ложное
        + _spell(210, 20, with_iv=True)
    )
    # Интервенция внутри четвёртого спелла
    interventions = [{"ts": 215}]

    costs = Costs(c_stuck=1.0, c_intervention=1.0, c_false=10.0)
    res = compute_J(samples, interventions, costs)
    assert res.n_false == 1, f"ожидалось 1 ложное, получено {res.n_false}"
    # Убеждаемся, что штраф вошёл в J
    assert res.J > res.bad_duration + res.n_interventions * costs.c_intervention
