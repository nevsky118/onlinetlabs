"""Shared helpers reused across multiple agents."""


def format_failing_check(failing_check: dict) -> str:
    """Format a failed spec check into a string for the LLM prompt."""
    params = failing_check.get("params")
    node = params.get("node") if isinstance(params, dict) else None
    node_str = f" на {node}" if node else ""
    return (
        f"Провалившаяся проверка {failing_check.get('kind')}{node_str}: "
        f"ожидалось {failing_check.get('expected')}, получено {failing_check.get('actual')}."
    )
