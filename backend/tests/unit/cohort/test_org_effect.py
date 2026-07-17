import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_is_none

from cohort.metrics import LearnerOutcome, org_effect_trend, SURVIVORSHIP_NOTE

pytestmark = [pytest.mark.unit]


def _rec(reached, l1e, l2e, l1r, l2r):
    return LearnerOutcome(
        user_id="u",
        skill="s",
        arm="closed",
        reached_l2=reached,
        time_to_l2_seconds=10.0 if reached else None,
        active_seconds=None,
        sessions_to_l2=1,
        l1_interventions=0,
        l2_interventions=0,
        l1_escalations=l1e,
        l2_escalations=l2e,
        l1_repeated_errors=l1r,
        l2_repeated_errors=l2r,
        observation_seconds=100.0,
        censored=not reached,
    )


class TestOrgEffect:
    @autotest.num("852")
    @autotest.external_id("bf4b4d6e-c9a4-40e3-ad32-a980ebf91b16")
    @autotest.name("OrgEffect: описательный тренд и survivorship-пометка")
    def test_bf4b4d6e_trend_descriptive_and_tagged(self):
        with autotest.step("Arrange: 2 записи с разными эскалациями"):
            recs = [_rec(True, 2, 0, 3, 1), _rec(True, 3, 1, 2, 0)]
        with autotest.step("Act: org_effect_trend"):
            t = org_effect_trend(recs)
        with autotest.step("Assert: средние и survivorship-нота корректны"):
            assert_equal(t.l1_escalations_mean, 2.5, "l1_escalations_mean == 2.5")
            assert_equal(t.l2_escalations_mean, 0.5, "l2_escalations_mean == 0.5")
            assert_equal(t.l1_repeated_errors_mean, 2.5, "l1_repeated_errors_mean == 2.5")
            assert_equal(t.l2_repeated_errors_mean, 0.5, "l2_repeated_errors_mean == 0.5")
            assert_true("описатель" in t.note.lower(), "нота помечена как описательная")
            assert_equal(t.note, SURVIVORSHIP_NOTE, "нота == SURVIVORSHIP_NOTE")

    @autotest.num("853")
    @autotest.external_id("88f109b7-6e44-4688-81ff-866f0528f2c8")
    @autotest.name("OrgEffect: l2_means None при отсутствии L2-данных")
    def test_88f109b7_l2_means_none_when_no_l2(self):
        with autotest.step("Arrange: 1 запись без L2 (не дошёл)"):
            recs = [_rec(False, 5, None, 4, None)]
        with autotest.step("Act: org_effect_trend"):
            t = org_effect_trend(recs)
        with autotest.step("Assert: l2_escalations_mean is None"):
            assert_is_none(t.l2_escalations_mean, "l2_escalations_mean None при отсутствии L2")
