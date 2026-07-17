import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from cohort.metrics import LearnerOutcome, aggregate_cohort

pytestmark = [pytest.mark.unit]


class TestCohortEndpoint:
    @autotest.num("1002")
    @autotest.external_id("af57dc57-575a-40e2-8b81-b0b82b2efaa4")
    @autotest.name("cohort_response_from_result: пустая когорта — headline=closed, pooled.n==0")
    def test_af57dc57_cohort_response_from_result(self):
        from instructor.schemas import cohort_response_from_result

        with autotest.step("Act: агрегировать пустую когорту и построить ответ"):
            out = aggregate_cohort([], horizon_seconds=100.0, by_arm=False)
            resp = cohort_response_from_result(out)

        with autotest.step("Assert: headline_arm и pooled.n"):
            assert_equal(resp.headline_arm, "closed", "headline_arm=closed")
            assert_equal(resp.pooled.n, 0, "pooled.n==0")

    @autotest.num("1003")
    @autotest.external_id("c32c4035-172e-4ec2-a2b0-eb75dc3a0a0c")
    @autotest.name(
        "cohort_response_from_result: один достигший L2 — by_skill, reach_rate, note сохраняются"
    )
    def test_c32c4035_cohort_response_non_empty(self):
        from instructor.schemas import cohort_response_from_result

        with autotest.step("Arrange: один учащийся, достигший L2"):
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

        with autotest.step("Act: агрегировать и построить ответ"):
            out = aggregate_cohort([rec], horizon_seconds=7200.0, by_arm=False)
            resp = cohort_response_from_result(out)

        with autotest.step("Assert: by_skill содержит ячейку routing"):
            assert_equal(len(resp.by_skill), 1, "одна ячейка в by_skill")
            cell = resp.by_skill[0]
            assert_equal(cell.skill, "routing", "skill=routing")
            assert_equal(cell.n, 1, "n=1")

        with autotest.step("Assert: reach_rate и reach_rate_at_horizon"):
            assert_equal(cell.time_to_competence.reach_rate, 1.0, "reach_rate=1.0")
            assert_equal(
                cell.time_to_competence.reach_rate_at_horizon, 1.0, "reach_rate_at_horizon=1.0"
            )

        with autotest.step("Assert: note survivorship-guard содержит 'описатель'"):
            assert_true("описатель" in cell.org_effect.note.lower(), "note содержит 'описатель'")
