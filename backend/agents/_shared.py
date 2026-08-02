"""Shared helpers reused across multiple agents."""

from i18n import Locale, t


def format_failing_check(failing_check: dict, locale: Locale) -> str:
    """Format a failed spec check into a string for the LLM prompt."""
    params = failing_check.get("params")
    node = params.get("node") if isinstance(params, dict) else None
    node_clause = t("prompt.failing_check_node", locale, node=node) if node else ""
    return t(
        "prompt.failing_check",
        locale,
        kind=failing_check.get("kind"),
        node=node_clause,
        expected=failing_check.get("expected"),
        actual=failing_check.get("actual"),
    )


def language_directive(locale: Locale) -> str:
    """Explicit response-language instruction appended to every system prompt."""
    return t("prompt.language_directive", locale)
