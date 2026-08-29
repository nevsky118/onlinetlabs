import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true

from analytics.cohort.metrics import kaplan_meier_median, reach_rate_at, restricted_mean

pytestmark = [pytest.mark.unit]


class TestKaplanMeier:
    @autotest.num("792")
    @autotest.external_id("d4657c96-fcea-474e-be08-300246db99f7")
    @autotest.name("KaplanMeier: median with all events, no censoring")
    def test_d4657c96_median_all_events_no_censor(self):
        with autotest.step("Arrange: 4 events at 10,20,30,40"):
            durations = [10.0, 20.0, 30.0, 40.0]
            observed = [True, True, True, True]
        with autotest.step("Act: compute the median"):
            result = kaplan_meier_median(durations, observed)
        with autotest.step("Assert: median == 30.0"):
            assert_equal(result, 30.0, "median falls between 20 and 30 by the KM step")

    @autotest.num("793")
    @autotest.external_id("2cb77ae5-5eb5-4e01-b300-331abbeb162e")
    @autotest.name("KaplanMeier: median is None when most are censored")
    def test_2cb77ae5_median_none_when_majority_censored(self):
        with autotest.step("Arrange: 1 event, 3 censored early"):
            durations = [10.0, 5.0, 6.0, 7.0]
            observed = [True, False, False, False]
        with autotest.step("Act: compute the median"):
            result = kaplan_meier_median(durations, observed)
        with autotest.step("Assert: S never reaches 0.5 → None"):
            assert_is_none(result, "median is undefined")

    @autotest.num("794")
    @autotest.external_id("35b05af7-109d-4ee7-a6d0-701f40fb54c8")
    @autotest.name("KaplanMeier: reach_rate_at at the horizon")
    def test_35b05af7_reach_rate_at_horizon(self):
        with autotest.step("Arrange: 2 of 4 reached by T=25"):
            durations = [10.0, 20.0, 5.0, 40.0]
            observed = [True, True, False, True]
        with autotest.step("Act: reach_rate_at horizon=25"):
            reach = reach_rate_at(durations, observed, horizon=25.0)
        with autotest.step("Assert: rate within range and ≈0.5"):
            assert_true(0.0 < reach < 1.0, "rate within the valid range")
            assert_equal(reach, pytest.approx(0.5, abs=0.2), "rate ≈ 0.5")

    @autotest.num("795")
    @autotest.external_id("a8749ba2-e808-4201-ae80-011c4bf9b63d")
    @autotest.name("KaplanMeier: restricted_mean is positive")
    def test_a8749ba2_restricted_mean_positive(self):
        with autotest.step("Arrange: 3 events"):
            durations = [10.0, 20.0, 30.0]
            observed = [True, True, True]
        with autotest.step("Act: restricted_mean horizon=30"):
            rm = restricted_mean(durations, observed, horizon=30.0)
        with autotest.step("Assert: 0 < rm <= 30"):
            assert_true(0.0 < rm <= 30.0, "restricted mean is positive and within the horizon")

    @autotest.num("796")
    @autotest.external_id("a2e72872-5e14-43d4-a438-0f4e89bfce69")
    @autotest.name("KaplanMeier: empty inputs are safe")
    def test_a2e72872_empty_inputs_safe(self):
        with autotest.step("Act + Assert: empty lists do not raise"):
            assert_is_none(kaplan_meier_median([], []), "median on empty is None")
            assert_equal(reach_rate_at([], [], 10.0), 0.0, "reach_rate on empty is 0.0")
            assert_equal(restricted_mean([], [], 10.0), 0.0, "restricted_mean on empty is 0.0")

    @autotest.num("797")
    @autotest.external_id("5ab5f95c-ad98-435a-bb46-27a232559827")
    @autotest.name("KaplanMeier: median when the crossing happens on the last event")
    def test_5ab5f95c_median_when_crossing_event_is_last(self):
        with autotest.step("Act: d=[10,20], both events"):
            result = kaplan_meier_median([10.0, 20.0], [True, True])
        with autotest.step("Assert: median == 20.0"):
            assert_equal(result, 20.0, "median at the last event")

    @autotest.num("798")
    @autotest.external_id("6d930fad-406a-43cd-b3f4-654fd1fd6ec1")
    @autotest.name("KaplanMeier: median is None when reach is below half")
    def test_6d930fad_median_none_when_reach_below_half(self):
        with autotest.step("Act: 2 of 5 reached"):
            result = kaplan_meier_median(
                [10.0, 20.0, 30.0, 40.0, 50.0],
                [True, True, False, False, False],
            )
        with autotest.step("Assert: median is undefined"):
            assert_is_none(result, "reach_rate < 0.5 → None")
