"""Общий статистический хелпер: единая перцентиль-конвенция для evaluation и learning_analytics."""

import statistics


def percentile(data: list[float], p: float) -> float:
    """Перцентиль p (0-100) по стандартной линейной интерполяции.

    Hyndman-Fan Type 7 (numpy/R/pandas default) — единственная конвенция в проекте.
    """
    if not data:
        return 0.0
    if len(data) == 1:
        return float(data[0])
    return statistics.quantiles(data, n=100, method="inclusive")[int(p) - 1]
