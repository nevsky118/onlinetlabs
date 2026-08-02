"""HintAgent models."""

from pydantic import BaseModel, Field

from i18n import DEFAULT_LOCALE, Locale
from learning_analytics.context import AgentContext


class HintInput(BaseModel):
    """Hint request."""

    session_id: str
    user_id: str
    lab_slug: str
    step_slug: str
    attempts_count: int = Field(default=0, ge=0)
    last_error: str | None = None
    failing_check: dict | None = None
    agent_context: AgentContext | None = None
    locale: Locale = DEFAULT_LOCALE


class HintResponse(BaseModel):
    """Hint from the agent."""

    hint: str
    hint_level: int = Field(ge=1, le=3, description="1=general, 2=guiding, 3=specific")
    remaining_hints: int = Field(ge=0)
