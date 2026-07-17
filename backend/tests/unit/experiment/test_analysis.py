import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_greater, assert_true

from experiment.analysis import compute_experiment_analysis
from tests.settings.data.experiment_data import ExperimentMetricsData

pytestmark = [pytest.mark.unit]


class TestAnalysis:
    @autotest.num("620")
    @autotest.external_id("e7fc78f1-1cec-4410-b468-c32073420c28")
    @autotest.name("compute_experiment_analysis: значимая разница")
    def test_e7fc78f1_significant_difference(self):
        # Arrange
        with autotest.step("Создаём данные с явной разницей"):
            group_a = [ExperimentMetricsData("group_a", 2400, 10, 8) for _ in range(20)]
            group_b = [ExperimentMetricsData("group_b", 1600, 5, 3, 4) for _ in range(20)]
            all_metrics = group_a + group_b

        # Act
        with autotest.step("Вычисляем анализ"):
            result = compute_experiment_analysis(all_metrics)

        # Assert
        with autotest.step("Проверяем результат"):
            assert_equal(result["sample_size"]["group_a"], 20, "20 group_a")
            assert_equal(result["sample_size"]["group_b"], 20, "20 group_b")
            assert_equal(result["h1_time_to_completion"]["group_a_mean"], 2400, "group_a mean")
            assert_equal(result["h1_time_to_completion"]["group_b_mean"], 1600, "group_b mean")
            assert_greater(
                result["h1_time_to_completion"]["reduction_percent"],
                0,
                "время сократилось",
            )
            assert_greater(
                result["h2_repeated_errors"]["reduction_percent"],
                0,
                "ошибки сократились",
            )
            assert_true(result["h1_time_to_completion"]["significant"], "разница значима")

    @autotest.num("621")
    @autotest.external_id("3963811d-ba05-4fc7-8b84-17f6b29e922e")
    @autotest.name("compute_experiment_analysis: малая выборка")
    def test_3963811d_small_sample(self):
        # Arrange
        with autotest.step("Создаём данные с 1 участником в группе"):
            all_metrics = [
                ExperimentMetricsData("group_a", 2400, 10, 8),
                ExperimentMetricsData("group_b", 1600, 5, 3),
            ]

        # Act
        with autotest.step("Анализ не падает"):
            result = compute_experiment_analysis(all_metrics)

        # Assert
        with autotest.step("sample_size корректный"):
            assert_equal(result["sample_size"]["group_a"], 1, "1 group_a")
            assert_equal(result["sample_size"]["group_b"], 1, "1 group_b")
            assert_true("error" in result["h1_time_to_completion"], "h1 содержит error")
