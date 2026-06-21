import pytest

from cohort.metrics import LearnerOutcome, aggregate_cohort

pytestmark = [pytest.mark.unit]


def test_cohort_response_from_result():
    """Пустая когорта: headline=closed, pooled.n==0."""
    from instructor.schemas import cohort_response_from_result

    out = aggregate_cohort([], horizon_seconds=100.0, by_arm=False)
    resp = cohort_response_from_result(out)
    assert resp.headline_arm == "closed"
    assert resp.pooled.n == 0


def test_cohort_response_non_empty():
    """Один достигший L2: by_skill, reach_rate, note-строки сохраняются."""
    from instructor.schemas import cohort_response_from_result

    rec = LearnerOutcome(
        user_id="u1",
        skill="routing",
        arm="closed",
        reached_l2=True,
        time_to_l2_seconds=3600.0,
        active_seconds=1800.0,
        sessions_to_l2=2,
        l1_interventions=3,
        l2_interventions=0,
        l1_escalations=1,
        l2_escalations=0,
        l1_repeated_errors=2,
        l2_repeated_errors=0,
        observation_seconds=3600.0,
        censored=False,
    )
    out = aggregate_cohort([rec], horizon_seconds=7200.0, by_arm=False)
    resp = cohort_response_from_result(out)

    assert len(resp.by_skill) == 1
    cell = resp.by_skill[0]
    assert cell.skill == "routing"
    assert cell.n == 1
    assert cell.time_to_competence.reach_rate == 1.0
    assert cell.time_to_competence.reach_rate_at_horizon == 1.0
    # note-строки survivorship-guard передаются как есть
    assert "описатель" in cell.org_effect.note.lower()
