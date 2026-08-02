"""Pure assembly of the chat tutor's system prompt."""

from agents._shared import language_directive
from i18n import Locale, t

# Structural anchors. ASCII and identical in every locale so the prompt body and the
# assembled sections can never drift apart.
TASK_MARKER = "[TASK]"
LAB_STATE_MARKER = "[LAB_STATE]"


def build_system_content(locale: Locale, lab_ctx: str | None, mcp_ctx: str | None) -> str:
    """System prompt plus whichever context sections are available."""
    parts = [f"{t('prompt.tutor.chat_system', locale)}\n\n{language_directive(locale)}"]
    if lab_ctx:
        parts.append(f"{TASK_MARKER}\n{lab_ctx}")
    if mcp_ctx:
        parts.append(f"{LAB_STATE_MARKER}\n{mcp_ctx}")
    return "\n\n".join(parts)
