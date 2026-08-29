import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true

from analytics.cohort.metrics import RETENTION_NOTE, retention_metric

pytestmark = [pytest.mark.unit]


class TestRetention:
    @autotest.num("912")
    @autotest.external_id("ad40b2b6-9b02-4b98-92c6-83f125cabacc")
    @autotest.name("Retention: rate and bias note when data is present")
    def test_ad40b2b6_retention_rate_and_flag(self):
        with autotest.step("Act: retention_metric [True, True, False]"):
            retention = retention_metric([True, True, False])
        with autotest.step("Assert: count=3, rate≈2/3, note is correct"):
            assert_equal(retention.retest_count, 3, "retest_count == 3")
            assert_equal(retention.retest_pass_rate, pytest.approx(2 / 3), "rate ≈ 2/3")
            assert_true(
                "предварит" in retention.note.lower() or "смещ" in retention.note.lower(),
                "note contains a keyword",
            )
            assert_equal(retention.note, RETENTION_NOTE, "note == RETENTION_NOTE")

    @autotest.num("913")
    @autotest.external_id("4f023f3a-7da3-45a5-85fe-05ed601b3584")
    @autotest.name("Retention: empty list is safe")
    def test_4f023f3a_retention_empty(self):
        with autotest.step("Act: retention_metric []"):
            retention = retention_metric([])
        with autotest.step("Assert: count=0, rate=None"):
            assert_equal(retention.retest_count, 0, "retest_count == 0")
            assert_is_none(retention.retest_pass_rate, "rate is None on empty")
