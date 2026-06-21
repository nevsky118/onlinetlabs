import pytest
from cohort.metrics import LearnerOutcome, org_effect_trend, SURVIVORSHIP_NOTE
pytestmark = [pytest.mark.unit]

def _rec(reached, l1e, l2e, l1r, l2r):
    return LearnerOutcome(
        user_id="u", skill="s", arm="closed", reached_l2=reached,
        time_to_l2_seconds=10.0 if reached else None, active_seconds=None, sessions_to_l2=1,
        l1_interventions=0, l2_interventions=0, l1_escalations=l1e, l2_escalations=l2e,
        l1_repeated_errors=l1r, l2_repeated_errors=l2r, observation_seconds=100.0,
        censored=not reached,
    )

def test_trend_descriptive_and_tagged():
    recs = [_rec(True, 2, 0, 3, 1), _rec(True, 3, 1, 2, 0)]
    t = org_effect_trend(recs)
    assert t.l1_escalations_mean == 2.5
    assert t.l2_escalations_mean == 0.5
    assert t.l1_repeated_errors_mean == 2.5
    assert t.l2_repeated_errors_mean == 0.5
    # survivorship-guard: пометка обязательна и явно «описательный»
    assert "описатель" in t.note.lower()
    assert t.note == SURVIVORSHIP_NOTE

def test_l2_means_none_when_no_l2():
    recs = [_rec(False, 5, None, 4, None)]
    t = org_effect_trend(recs)
    assert t.l2_escalations_mean is None
