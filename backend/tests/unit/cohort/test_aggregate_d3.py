import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_is_none

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


class TestAggregateD3:
    @autotest.num("822")
    @autotest.external_id("5d00fd88-cff6-48a4-b41d-138672a194b6")
    @autotest.name("AggregateD3: time_to_competence с цензурированием")
    def test_5d00fd88_time_to_competence_with_censoring(self):
        with autotest.step("Arrange: 2 дошли, 1 цензурирован"):
            recs = [_rec(True, 10.0), _rec(True, 20.0), _rec(False, None, obs=15.0)]
        with autotest.step("Act: time_to_competence horizon=25"):
            r = time_to_competence(recs, horizon_seconds=25.0)
        with autotest.step("Assert: n=3, censored=1, reach_rate в диапазоне"):
            assert_equal(r.n, 3, "n == 3")
            assert_equal(r.censored, 1, "censored == 1")
            assert_true(0.0 < r.reach_rate < 1.0, "не все дошли")
            assert_true(r.reach_rate_at_horizon > 0.0, "reach_rate_at_horizon > 0")

    @autotest.num("823")
    @autotest.external_id("3e0df427-d93d-45f6-b449-2249fbd9b614")
    @autotest.name("AggregateD3: медиана None при малой выборке достигших")
    def test_3e0df427_median_none_on_sparse(self):
        with autotest.step("Arrange: 1 дошёл, 3 цензурированы рано"):
            recs = [_rec(True, 50.0)] + [_rec(False, None, obs=5.0) for _ in range(3)]
        with autotest.step("Act: time_to_competence horizon=100"):
            r = time_to_competence(recs, horizon_seconds=100.0)
        with autotest.step("Assert: median None, reach_rate ≈ 0.25"):
            assert_is_none(r.median_calendar_seconds, "медиана не определена")
            assert_equal(r.reach_rate, pytest.approx(0.25, abs=0.01), "reach_rate ≈ 0.25")

    @autotest.num("824")
    @autotest.external_id("13b0bfea-d383-4e22-b9df-9ed6da4e50cc")
    @autotest.name("AggregateD3: autonomy_metrics при L2=0")
    def test_13b0bfea_autonomy_l2_lower(self):
        with autotest.step("Arrange: 1 запись, l1i=3, l2i=0, sessions=2"):
            recs = [_rec(True, 10.0, sessions=2, l1i=3, l2i=0)]
        with autotest.step("Act: autonomy_metrics"):
            a = autonomy_metrics(recs)
        with autotest.step("Assert: средние интервенции корректны"):
            assert_equal(a.mean_l1_interventions, 3.0, "mean_l1 == 3.0")
            assert_equal(a.mean_l2_interventions, 0.0, "mean_l2 == 0.0")
            assert_equal(a.mean_sessions_to_l2, 2.0, "mean_sessions == 2.0")
