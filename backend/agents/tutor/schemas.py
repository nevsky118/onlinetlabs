"""TutorAgent models."""

from pydantic import BaseModel, Field

from analytics.runtime.context import AgentContext
from i18n import DEFAULT_LOCALE, Locale


class TutorInput(BaseModel):
    """Student's question to the tutor."""

    session_id: str
    user_id: str
    question: str
    context: str = Field(default="", description="Lab/course context")
    lab_slug: str | None = None
    step_slug: str | None = None
    failing_check: dict | None = None
    agent_context: AgentContext | None = None
    locale: Locale = DEFAULT_LOCALE


class TutorResponse(BaseModel):
    """Tutor's answer."""

    answer: str
    follow_up_questions: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
