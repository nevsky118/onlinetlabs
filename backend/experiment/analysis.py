"""Встроенный статистический анализ эксперимента."""

import math

from experiment.group_assigner import ExperimentGroup


def compute_experiment_analysis(all_metrics: list) -> dict:
    """Метрики → статистический анализ по гипотезам H1, H2."""
    group_a = [m for m in all_metrics if m.experiment_group == ExperimentGroup.GROUP_A]
    group_b = [m for m in all_metrics if m.experiment_group == ExperimentGroup.GROUP_B]

    result = {
        "sample_size": {
            "group_a": len(group_a),
            "group_b": len(group_b),
        },
    }

    if len(group_a) >= 2 and len(group_b) >= 2:
        result["h1_time_to_completion"] = _compare_groups(
            [m.total_time_seconds for m in group_a],
            [m.total_time_seconds for m in group_b],
        )
        result["h2_repeated_errors"] = _compare_groups(
            [m.repeated_errors for m in group_a],
            [m.repeated_errors for m in group_b],
        )
    else:
        result["h1_time_to_completion"] = _insufficient_data()
        result["h2_repeated_errors"] = _insufficient_data()

    return result


def _compare_groups(group_a_values: list[float], group_b_values: list[float]) -> dict:
    """t-статистика Welch + p-value с нормальной аппроксимацией + Cohen's d."""
    group_a_mean = sum(group_a_values) / len(group_a_values)
    group_b_mean = sum(group_b_values) / len(group_b_values)

    t_stat, p_value = _welch_ttest_normal_approx(group_a_values, group_b_values)
    cohens_d = _cohens_d(group_a_values, group_b_values)

    reduction = (
        ((group_a_mean - group_b_mean) / group_a_mean * 100)
        if group_a_mean != 0
        else 0.0
    )

    return {
        "group_a_mean": round(group_a_mean, 2),
        "group_b_mean": round(group_b_mean, 2),
        "reduction_percent": round(reduction, 1),
        "t_statistic": round(float(t_stat), 4),
        "p_value": round(float(p_value), 4),
        "cohens_d": round(cohens_d, 4),
        "significant": p_value < 0.05,
    }


def _welch_ttest_normal_approx(
    group1: list[float], group2: list[float]
) -> tuple[float, float]:
    """Двусторонний t-test без scipy, с нормальной аппроксимацией для p-value."""
    mean1 = sum(group1) / len(group1)
    mean2 = sum(group2) / len(group2)
    var1 = _sample_variance(group1)
    var2 = _sample_variance(group2)
    standard_error = math.sqrt(var1 / len(group1) + var2 / len(group2))
    if standard_error == 0:
        if mean1 == mean2:
            return 0.0, 1.0
        return 1_000_000.0, 0.0
    t_stat = (mean1 - mean2) / standard_error
    p_value = math.erfc(abs(t_stat) / math.sqrt(2))
    return t_stat, p_value


def _sample_variance(values: list[float]) -> float:
    """Выборочная дисперсия."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / (len(values) - 1)


def _cohens_d(group1: list[float], group2: list[float]) -> float:
    """Размер эффекта Cohen's d."""
    n1, n2 = len(group1), len(group2)
    mean1 = sum(group1) / n1
    mean2 = sum(group2) / n2
    var1 = sum((x - mean1) ** 2 for x in group1) / max(n1 - 1, 1)
    var2 = sum((x - mean2) ** 2 for x in group2) / max(n2 - 1, 1)
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / max(n1 + n2 - 2, 1))
    return abs(mean1 - mean2) / pooled_std if pooled_std > 0 else 0.0


def _insufficient_data() -> dict:
    """Заглушка при недостаточной выборке."""
    return {
        "group_a_mean": None,
        "group_b_mean": None,
        "reduction_percent": None,
        "t_statistic": None,
        "p_value": None,
        "cohens_d": None,
        "significant": None,
        "error": "Недостаточно данных (нужно >= 2 участников в каждой группе)",
    }
