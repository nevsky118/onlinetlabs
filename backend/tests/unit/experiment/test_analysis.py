import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_greater

from experiment.analysis import compute_experiment_analysis
from tests.settings.data.experiment_data import ExperimentMetricsData

pytestmark = [pytest.mark.unit]


class TestAnalysis:
    @autotest.num("620")
    @autotest.external_id("e5f6a7b8-c9d0-4123-efab-620000000005")
    @autotest.name("compute_experiment_analysis: значимая разница")
    def test_e5f6a7b8_significant_difference(self):
        with autotest.step("Создаём данные с явной разницей"):
            control = [ExperimentMetricsData("control", 2400, 10, 8) for _ in range(20)]
            experimental = [ExperimentMetricsData("experimental", 1600, 5, 3, 4) for _ in range(20)]
            all_metrics = control + experimental

        with autotest.step("Вычисляем анализ"):
            result = compute_experiment_analysis(all_metrics)

        with autotest.step("Проверяем результат"):
            assert_equal(result["sample_size"]["control"], 20, "20 control")
            assert_equal(result["sample_size"]["experimental"], 20, "20 experimental")
            assert_greater(result["h1_time_to_completion"]["reduction_percent"], 0, "время сократилось")
            assert_greater(result["h2_repeated_errors"]["reduction_percent"], 0, "ошибки сократились")

    @autotest.num("621")
    @autotest.external_id("f6a7b8c9-d0e1-4234-fabc-621000000006")
    @autotest.name("compute_experiment_analysis: малая выборка")
    def test_f6a7b8c9_small_sample(self):
        with autotest.step("Создаём данные с 1 участником в группе"):
            all_metrics = [
                ExperimentMetricsData("control", 2400, 10, 8),
                ExperimentMetricsData("experimental", 1600, 5, 3),
            ]

        with autotest.step("Анализ не падает"):
            result = compute_experiment_analysis(all_metrics)

        with autotest.step("sample_size корректный"):
            assert_equal(result["sample_size"]["control"], 1, "1 control")
            assert_true("error" in result["h1_time_to_completion"], "h1 содержит error")
