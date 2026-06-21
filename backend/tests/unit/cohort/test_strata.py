import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_is_none

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


class TestStrata:
    @autotest.num("882")
    @autotest.external_id("c83f9522-b9b1-48f2-9f85-a0311b5422a0")
    @autotest.name("Strata: by_skill и pooled с корректным n")
    def test_c83f9522_by_skill_and_pooled_with_n(self):
        with autotest.step("Arrange: ip×2 + dhcp×1"):
            recs = [
                _rec("ip", "closed", True, 10.0),
                _rec("ip", "closed", False, None),
                _rec("dhcp", "closed", True, 20.0),
            ]
        with autotest.step("Act: aggregate_cohort horizon=50"):
            out = aggregate_cohort(recs, horizon_seconds=50.0)
        with autotest.step("Assert: by_skill n корректен, pooled=3, by_arm=None"):
            skills = {c.skill: c for c in out["by_skill"]}
            assert_equal(skills["ip"].n, 2, "ip.n == 2")
            assert_equal(skills["dhcp"].n, 1, "dhcp.n == 1")
            assert_equal(out["pooled"].n, 3, "pooled.n == 3")
            assert_equal(out["headline_arm"], "closed", "headline_arm == closed")
            assert_is_none(out["by_arm"], "by_arm не запрошен → None")

    @autotest.num("883")
    @autotest.external_id("a0feb36f-5c7b-4d8f-b6f6-70d29d0e6c64")
    @autotest.name("Strata: by_arm опциональная страта")
    def test_a0feb36f_by_arm_optional_stratum(self):
        with autotest.step("Arrange: ip closed + ip open"):
            recs = [_rec("ip", "closed", True, 10.0), _rec("ip", "open", False, None)]
        with autotest.step("Act: aggregate_cohort by_arm=True"):
            out = aggregate_cohort(recs, horizon_seconds=50.0, by_arm=True)
        with autotest.step("Assert: by_arm содержит closed и open"):
            arms = {c.arm: c for c in out["by_arm"]}
            assert_equal(set(arms), {"closed", "open"}, "оба плеча присутствуют")
            assert_equal(out["headline_arm"], "closed", "headline_arm == closed")
