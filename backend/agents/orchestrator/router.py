"""Routes requests to agents."""

INTENT_TO_AGENT = {
    "hint": "hint",
    "intervene_hint": "hint",
    "intervene_tutor": "tutor",
}


def resolve_agent(intent: str) -> str | None:
    """Determine the target agent from intent."""
    return INTENT_TO_AGENT.get(intent)
