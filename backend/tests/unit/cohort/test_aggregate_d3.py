import pytest
from cohort.metrics import LearnerOutcome, time_to_competence, autonomy_metrics
pytestmark = [pytest.mark.unit]

def _rec(reached, ttl, active=None, sessions=None, l1i=1, l2i=0, obs=100.0):
    return LearnerOutcome(
        user_id="u", skill="s", arm="closed", reached_l2=reached,
        time_to_l2_seconds=ttl, active_seconds=active, sessions_to_l2=sessions,
        l1_interventions=l1i, l2_interventions=l2i, l1_escalations=0, l2_escalations=0,
        l1_repeated_errors=0, l2_repeated_errors=0, observation_seconds=obs,
        censored=not reached,
    )

def test_time_to_competence_with_censoring():
    recs = [_rec(True, 10.0), _rec(True, 20.0), _rec(False, None, obs=15.0)]
    r = time_to_competence(recs, horizon_seconds=25.0)
    assert r.n == 3
    assert r.censored == 1
    assert 0.0 < r.reach_rate < 1.0      # не все дошли
    assert r.reach_rate_at_horizon > 0.0

def test_median_none_on_sparse():
    recs = [_rec(True, 50.0)] + [_rec(False, None, obs=5.0) for _ in range(3)]
    r = time_to_competence(recs, horizon_seconds=100.0)
    assert r.median_calendar_seconds is None   # фолбэк: reach_rate всё равно есть
    assert r.reach_rate == pytest.approx(0.25, abs=0.01)

def test_autonomy_l2_lower():
    recs = [_rec(True, 10.0, sessions=2, l1i=3, l2i=0)]
    a = autonomy_metrics(recs)
    assert a.mean_l1_interventions == 3.0
    assert a.mean_l2_interventions == 0.0
    assert a.mean_sessions_to_l2 == 2.0
