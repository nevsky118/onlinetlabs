"""Маршрутизация запросов к агентам."""

INTENT_TO_AGENT = {
    "question": "tutor",
    "validate": "validator",
    "hint": "hint",
    "lab": "lab",
    "analytics": "analytics",
}


def resolve_agent(intent: str) -> str | None:
    """Определить целевого агента по intent."""
    return INTENT_TO_AGENT.get(intent)
