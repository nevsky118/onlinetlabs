import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_is_none

from cohort.metrics import retention_metric, RETENTION_NOTE

pytestmark = [pytest.mark.unit]


class TestRetention:
    @autotest.num("912")
    @autotest.external_id("ad40b2b6-9b02-4b98-92c6-83f125cabacc")
    @autotest.name("Retention: rate и смещение-нота при наличии данных")
    def test_ad40b2b6_retention_rate_and_flag(self):
        with autotest.step("Act: retention_metric [True, True, False]"):
            r = retention_metric([True, True, False])
        with autotest.step("Assert: count=3, rate≈2/3, нота корректна"):
            assert_equal(r.retest_count, 3, "retest_count == 3")
            assert_equal(r.retest_pass_rate, pytest.approx(2 / 3), "rate ≈ 2/3")
            assert_true(
                "предварит" in r.note.lower() or "смещ" in r.note.lower(),
                "нота содержит ключевое слово",
            )
            assert_equal(r.note, RETENTION_NOTE, "нота == RETENTION_NOTE")

    @autotest.num("913")
    @autotest.external_id("4f023f3a-7da3-45a5-85fe-05ed601b3584")
    @autotest.name("Retention: пустой список безопасен")
    def test_4f023f3a_retention_empty(self):
        with autotest.step("Act: retention_metric []"):
            r = retention_metric([])
        with autotest.step("Assert: count=0, rate=None"):
            assert_equal(r.retest_count, 0, "retest_count == 0")
            assert_is_none(r.retest_pass_rate, "rate None на пустом")
