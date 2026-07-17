"""Shared helpers reused across multiple agents."""


def format_failing_check(fc: dict) -> str:
    """Format a failed spec check into a string for the LLM prompt."""
    node = fc.get("params", {}).get("node") if isinstance(fc.get("params"), dict) else None
    node_str = f" на {node}" if node else ""
    return (
        f"Провалившаяся проверка {fc.get('kind')}{node_str}: "
        f"ожидалось {fc.get('expected')}, получено {fc.get('actual')}."
    )
