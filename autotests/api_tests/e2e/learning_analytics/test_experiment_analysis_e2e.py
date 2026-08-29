# E2E (Tier 2): compute_experiment_analysis computes H1/H2 per group.

import pytest

pytest.importorskip("pydantic_ai")  # Tier 2: runs only in the backend venv, otherwise a module-level skip

from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_equal, assert_in
from autotests.api.data.e2e.learning_analytics_data import ArmMetricData


@pytest.mark.e2e
@pytest.mark.asyncio
class TestExperimentAnalysisE2E:
    @autotest.num("3486")
    @autotest.external_id("d03ed47a-1fc8-4464-b3a9-bd3d4b4e7ee8")
    @autotest.name("E2E: compute_experiment_analysis returns H1/H2 for two groups")
    async def test_d03ed47a_analysis(self):
        with autotest.step("Arrange: build metrics for group A and group B"):
            from experiment.analysis import compute_experiment_analysis
            from experiment.assignment import ExperimentGroup

            metrics = (
                [ArmMetricData(ExperimentGroup.GROUP_A.value, 600.0, 5) for _ in range(4)]
                + [ArmMetricData(ExperimentGroup.GROUP_B.value, 400.0, 2) for _ in range(4)]
            )
        with autotest.step("Compute analysis"):
            res = compute_experiment_analysis(metrics)
        with autotest.step("Sample size and hypotheses present"):
            assert_equal(res["sample_size"]["group_a"], 4, "group a")
            assert_equal(res["sample_size"]["group_b"], 4, "group b")
            assert_in("h1_time_to_completion", res, "'h1_time_to_completion'")
            assert_in("h2_repeated_errors", res, "'h2_repeated_errors'")
