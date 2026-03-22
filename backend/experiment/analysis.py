"""Встроенный статистический анализ эксперимента."""

import math


def compute_experiment_analysis(all_metrics: list) -> dict:
    """Метрики → статистический анализ по гипотезам H1, H2."""
    control = [m for m in all_metrics if m.experiment_group == "control"]
    experimental = [m for m in all_metrics if m.experiment_group == "experimental"]

    result = {
        "sample_size": {
            "control": len(control),
            "experimental": len(experimental),
        },
    }

    if len(control) >= 2 and len(experimental) >= 2:
        result["h1_time_to_completion"] = _compare_groups(
            [m.total_time_seconds for m in control],
            [m.total_time_seconds for m in experimental],
        )
        result["h2_repeated_errors"] = _compare_groups(
            [m.repeated_errors for m in control],
            [m.repeated_errors for m in experimental],
        )
    else:
        result["h1_time_to_completion"] = _insufficient_data()
        result["h2_repeated_errors"] = _insufficient_data()

    return result


def _compare_groups(control_values: list[float], experimental_values: list[float]) -> dict:
    """t-test + Cohen's d между двумя группами."""
    from scipy.stats import ttest_ind

    control_mean = sum(control_values) / len(control_values)
    experimental_mean = sum(experimental_values) / len(experimental_values)

    t_stat, p_value = ttest_ind(control_values, experimental_values)
    cohens_d = _cohens_d(control_values, experimental_values)

    reduction = ((control_mean - experimental_mean) / control_mean * 100) if control_mean != 0 else 0.0

    return {
        "control_mean": round(control_mean, 2),
        "experimental_mean": round(experimental_mean, 2),
        "reduction_percent": round(reduction, 1),
        "t_statistic": round(float(t_stat), 4),
        "p_value": round(float(p_value), 4),
        "cohens_d": round(cohens_d, 4),
        "significant": p_value < 0.05,
    }


def _cohens_d(group1: list[float], group2: list[float]) -> float:
    """Effect size Cohen's d."""
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
        "control_mean": None,
        "experimental_mean": None,
        "reduction_percent": None,
        "t_statistic": None,
        "p_value": None,
        "cohens_d": None,
        "significant": None,
        "error": "Недостаточно данных (нужно >= 2 участников в каждой группе)",
    }
