import pytest
from cohort.metrics import kaplan_meier_median, reach_rate_at, restricted_mean
pytestmark = [pytest.mark.unit]

def test_median_all_events_no_censor():
    # 4 события на 10,20,30,40 → медиана между 20 и 30 (KM шаг): 30
    d = [10.0, 20.0, 30.0, 40.0]
    e = [True, True, True, True]
    assert kaplan_meier_median(d, e) == 30.0

def test_median_none_when_majority_censored():
    # 1 событие, 3 цензурированы рано → S не доходит до 0.5
    d = [10.0, 5.0, 6.0, 7.0]
    e = [True, False, False, False]
    assert kaplan_meier_median(d, e) is None

def test_reach_rate_at_horizon():
    # 2 из 4 достигли к T=25 (события на 10,20; цензур на 5; событие на 40)
    d = [10.0, 20.0, 5.0, 40.0]
    e = [True, True, False, True]
    r = reach_rate_at(d, e, horizon=25.0)
    assert 0.0 < r < 1.0 and r == pytest.approx(0.5, abs=0.2)

def test_restricted_mean_positive():
    d = [10.0, 20.0, 30.0]
    e = [True, True, True]
    rm = restricted_mean(d, e, horizon=30.0)
    assert 0.0 < rm <= 30.0

def test_empty_inputs_safe():
    assert kaplan_meier_median([], []) is None
    assert reach_rate_at([], [], 10.0) == 0.0
    assert restricted_mean([], [], 10.0) == 0.0

def test_median_when_crossing_event_is_last():
    # d=[10,20] оба события: S=0.5(t10),0(t20) → медиана 20 (не None)
    assert kaplan_meier_median([10.0, 20.0], [True, True]) == 20.0

def test_median_none_when_reach_below_half():
    # 2 из 5 дошли (<50%) → медиана не определена
    assert kaplan_meier_median([10.0, 20.0, 30.0, 40.0, 50.0],
                               [True, True, False, False, False]) is None
