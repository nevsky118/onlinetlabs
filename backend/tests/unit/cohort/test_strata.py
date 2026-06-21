import pytest
from cohort.metrics import LearnerOutcome, aggregate_cohort
pytestmark = [pytest.mark.unit]

def _rec(skill, arm, reached, ttl):
    return LearnerOutcome(
        user_id="u", skill=skill, arm=arm, reached_l2=reached,
        time_to_l2_seconds=ttl, active_seconds=ttl, sessions_to_l2=1 if reached else None,
        l1_interventions=1, l2_interventions=0 if reached else None,
        l1_escalations=1, l2_escalations=0 if reached else None,
        l1_repeated_errors=1, l2_repeated_errors=0 if reached else None,
        observation_seconds=100.0, censored=not reached,
    )

def test_by_skill_and_pooled_with_n():
    recs = [_rec("ip", "closed", True, 10.0), _rec("ip", "closed", False, None),
            _rec("dhcp", "closed", True, 20.0)]
    out = aggregate_cohort(recs, horizon_seconds=50.0)
    skills = {c.skill: c for c in out["by_skill"]}
    assert skills["ip"].n == 2 and skills["dhcp"].n == 1
    assert out["pooled"].n == 3
    assert out["headline_arm"] == "closed"
    assert out["by_arm"] is None   # by_arm не запрошен

def test_by_arm_optional_stratum():
    recs = [_rec("ip", "closed", True, 10.0), _rec("ip", "open", False, None)]
    out = aggregate_cohort(recs, horizon_seconds=50.0, by_arm=True)
    arms = {c.arm: c for c in out["by_arm"]}
    assert set(arms) == {"closed", "open"}
    assert out["headline_arm"] == "closed"
