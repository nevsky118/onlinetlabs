"""Shared statistics helper: a single percentile convention for evaluation and learning_analytics."""

import statistics


def percentile(data: list[float], p: float) -> float:
    """Percentile p (0-100) via standard linear interpolation.

    Hyndman-Fan Type 7 (numpy/R/pandas default) -- the only convention used in this project.
    """
    if not data:
        return 0.0
    if len(data) == 1:
        return float(data[0])
    return statistics.quantiles(data, n=100, method="inclusive")[int(p) - 1]
