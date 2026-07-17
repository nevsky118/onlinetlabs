import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true

from cohort.metrics import kaplan_meier_median, reach_rate_at, restricted_mean

pytestmark = [pytest.mark.unit]


class TestKaplanMeier:
    @autotest.num("792")
    @autotest.external_id("d4657c96-fcea-474e-be08-300246db99f7")
    @autotest.name("KaplanMeier: медиана при всех событиях без цензурирования")
    def test_d4657c96_median_all_events_no_censor(self):
        with autotest.step("Arrange: 4 события на 10,20,30,40"):
            d = [10.0, 20.0, 30.0, 40.0]
            e = [True, True, True, True]
        with autotest.step("Act: вычислить медиану"):
            result = kaplan_meier_median(d, e)
        with autotest.step("Assert: медиана == 30.0"):
            assert_equal(result, 30.0, "медиана между 20 и 30 по KM-шагу")

    @autotest.num("793")
    @autotest.external_id("2cb77ae5-5eb5-4e01-b300-331abbeb162e")
    @autotest.name("KaplanMeier: медиана None при большинстве цензурированных")
    def test_2cb77ae5_median_none_when_majority_censored(self):
        with autotest.step("Arrange: 1 событие, 3 цензурированы рано"):
            d = [10.0, 5.0, 6.0, 7.0]
            e = [True, False, False, False]
        with autotest.step("Act: вычислить медиану"):
            result = kaplan_meier_median(d, e)
        with autotest.step("Assert: S не доходит до 0.5 → None"):
            assert_is_none(result, "медиана не определена")

    @autotest.num("794")
    @autotest.external_id("35b05af7-109d-4ee7-a6d0-701f40fb54c8")
    @autotest.name("KaplanMeier: reach_rate_at на горизонте")
    def test_35b05af7_reach_rate_at_horizon(self):
        with autotest.step("Arrange: 2 из 4 достигли к T=25"):
            d = [10.0, 20.0, 5.0, 40.0]
            e = [True, True, False, True]
        with autotest.step("Act: reach_rate_at horizon=25"):
            r = reach_rate_at(d, e, horizon=25.0)
        with autotest.step("Assert: rate в диапазоне и ≈0.5"):
            assert_true(0.0 < r < 1.0, "rate в допустимом диапазоне")
            assert_equal(r, pytest.approx(0.5, abs=0.2), "rate ≈ 0.5")

    @autotest.num("795")
    @autotest.external_id("a8749ba2-e808-4201-ae80-011c4bf9b63d")
    @autotest.name("KaplanMeier: restricted_mean положительный")
    def test_a8749ba2_restricted_mean_positive(self):
        with autotest.step("Arrange: 3 события"):
            d = [10.0, 20.0, 30.0]
            e = [True, True, True]
        with autotest.step("Act: restricted_mean horizon=30"):
            rm = restricted_mean(d, e, horizon=30.0)
        with autotest.step("Assert: 0 < rm <= 30"):
            assert_true(0.0 < rm <= 30.0, "restricted mean положительный и в горизонте")

    @autotest.num("796")
    @autotest.external_id("a2e72872-5e14-43d4-a438-0f4e89bfce69")
    @autotest.name("KaplanMeier: пустые входы безопасны")
    def test_a2e72872_empty_inputs_safe(self):
        with autotest.step("Act + Assert: пустые списки не падают"):
            assert_is_none(kaplan_meier_median([], []), "median на пустом — None")
            assert_equal(reach_rate_at([], [], 10.0), 0.0, "reach_rate на пустом — 0.0")
            assert_equal(restricted_mean([], [], 10.0), 0.0, "restricted_mean на пустом — 0.0")

    @autotest.num("797")
    @autotest.external_id("5ab5f95c-ad98-435a-bb46-27a232559827")
    @autotest.name("KaplanMeier: медиана когда пересечение на последнем событии")
    def test_5ab5f95c_median_when_crossing_event_is_last(self):
        with autotest.step("Act: d=[10,20] оба события"):
            result = kaplan_meier_median([10.0, 20.0], [True, True])
        with autotest.step("Assert: медиана == 20.0"):
            assert_equal(result, 20.0, "медиана на последнем событии")

    @autotest.num("798")
    @autotest.external_id("6d930fad-406a-43cd-b3f4-654fd1fd6ec1")
    @autotest.name("KaplanMeier: медиана None когда reach ниже половины")
    def test_6d930fad_median_none_when_reach_below_half(self):
        with autotest.step("Act: 2 из 5 дошли"):
            result = kaplan_meier_median(
                [10.0, 20.0, 30.0, 40.0, 50.0],
                [True, True, False, False, False],
            )
        with autotest.step("Assert: медиана не определена"):
            assert_is_none(result, "reach_rate < 0.5 → None")
