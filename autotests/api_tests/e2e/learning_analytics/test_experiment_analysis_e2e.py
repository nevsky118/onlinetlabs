# E2E (Tier 2): compute_experiment_analysis считает H1/H2 по группам.

import pytest

pytest.importorskip("pydantic_ai")  # Tier 2: бежит только в backend-venv, иначе module-level skip

from autotests.settings.reports import autotest


def _metric(group: str, time_s: float, repeated: int):
    """Простая заглушка метрики — только поля, нужные analysis."""
    from experiment.group_assigner import ExperimentGroup

    class _M:
        experiment_group = group
        total_time_seconds = time_s
        repeated_errors = repeated

    return _M()


@pytest.mark.e2e
@pytest.mark.asyncio
class TestExperimentAnalysisE2E:
    @autotest.num("713")
    @autotest.external_id("a1b2c3d4-e5f6-7890-abcd-713000000001")
    @autotest.name("E2E: compute_experiment_analysis возвращает H1/H2 по двум группам")
    async def test_a1b2c3d4_analysis(self):
        from experiment.analysis import compute_experiment_analysis
        from experiment.group_assigner import ExperimentGroup

        metrics = (
            [_metric(ExperimentGroup.GROUP_A.value, 600.0, 5) for _ in range(4)]
            + [_metric(ExperimentGroup.GROUP_B.value, 400.0, 2) for _ in range(4)]
        )
        with autotest.step("Считаем анализ"):
            res = compute_experiment_analysis(metrics)
        with autotest.step("Размер выборки и гипотезы присутствуют"):
            assert res["sample_size"]["group_a"] == 4
            assert res["sample_size"]["group_b"] == 4
            assert "h1_time_to_completion" in res
            assert "h2_repeated_errors" in res
