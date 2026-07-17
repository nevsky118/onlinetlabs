"""Маршрутизация запросов к агентам."""

INTENT_TO_AGENT = {
    "hint": "hint",
    "intervene_hint": "hint",
    "intervene_tutor": "tutor",
}


def resolve_agent(intent: str) -> str | None:
    """Определить целевого агента по intent."""
    return INTENT_TO_AGENT.get(intent)
