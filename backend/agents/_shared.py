"""Общие хелперы, переиспользуемые несколькими агентами."""


def format_failing_check(fc: dict) -> str:
    """Отформатировать провалившуюся spec-проверку в строку для промпта LLM."""
    node = fc.get("params", {}).get("node") if isinstance(fc.get("params"), dict) else None
    node_str = f" на {node}" if node else ""
    return (
        f"Провалившаяся проверка {fc.get('kind')}{node_str}: "
        f"ожидалось {fc.get('expected')}, получено {fc.get('actual')}."
    )
