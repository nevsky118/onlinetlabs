"""percentile: unified Hyndman-Fan Type 7 convention, characterization on hand-computed fixtures."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from evaluation.stats import percentile

pytestmark = [pytest.mark.unit]


class TestPercentile:
    @autotest.num("2530")
    @autotest.external_id("4080bdf9-0d42-4a0f-8b38-3c135c880214")
    @autotest.name("percentile: p90 на 1..10 == 9.1 (Type 7, hand-computed)")
    def test_4080bdf9_p90_one_to_ten(self):
        with autotest.step("Arrange: data=1..10; h=(10-1)*0.9=8.1 → data[8]+0.1*(data[9]-data[8])"):
            data = list(range(1, 11))

        with autotest.step("Act: percentile(data, 90)"):
            result = percentile([float(x) for x in data], 90)

        with autotest.step("Assert: 9 + 0.1*(10-9) == 9.1"):
            assert_equal(result, 9.1, "p90(1..10) == 9.1")

    @autotest.num("2531")
    @autotest.external_id("5ab39d63-616b-498f-9912-fe966a1c45e8")
    @autotest.name("percentile: p90 на 1..5 == 4.6 (Type 7, hand-computed)")
    def test_5ab39d63_p90_one_to_five(self):
        with autotest.step("Arrange: data=1..5; h=(5-1)*0.9=3.6 → data[3]+0.6*(data[4]-data[3])"):
            data = list(range(1, 6))

        with autotest.step("Act: percentile(data, 90)"):
            result = percentile([float(x) for x in data], 90)

        with autotest.step("Assert: 4 + 0.6*(5-4) == 4.6"):
            assert_equal(result, 4.6, "p90(1..5) == 4.6")

    @autotest.num("2532")
    @autotest.external_id("75217610-f8aa-4d68-99cb-319a4910d448")
    @autotest.name("percentile: p50 на 1..10 == 5.5 (Type 7, hand-computed)")
    def test_75217610_p50_one_to_ten(self):
        with autotest.step("Arrange: data=1..10; h=(10-1)*0.5=4.5 → data[4]+0.5*(data[5]-data[4])"):
            data = list(range(1, 11))

        with autotest.step("Act: percentile(data, 50)"):
            result = percentile([float(x) for x in data], 50)

        with autotest.step("Assert: 5 + 0.5*(6-5) == 5.5"):
            assert_equal(result, 5.5, "p50(1..10) == 5.5")

    @autotest.num("2533")
    @autotest.external_id("4225c2f1-90f1-428f-a9a7-37b85892709f")
    @autotest.name("percentile: единственная точка возвращается как есть для любого p")
    def test_4225c2f1_single_point(self):
        with autotest.step("Arrange: data=[7.0]"):
            data = [7.0]

        with autotest.step("Act: percentile для p50 и p90"):
            p50 = percentile(data, 50)
            p90 = percentile(data, 90)

        with autotest.step("Assert: оба == 7.0 (нет интерполяции при n==1)"):
            assert_equal(p50, 7.0, "n==1 → p50 == единственное значение")
            assert_equal(p90, 7.0, "n==1 → p90 == единственное значение")

    @autotest.num("2534")
    @autotest.external_id("15da80aa-94e4-4c3d-9844-db18ab919bfc")
    @autotest.name("percentile: пустой вход → 0.0")
    def test_15da80aa_empty(self):
        with autotest.step("Act+Assert: percentile([], 90) == 0.0"):
            assert_equal(percentile([], 90), 0.0, "пусто → 0.0")
