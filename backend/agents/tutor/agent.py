"""Mentor agent that answers student questions."""

import logging

from agents._shared import format_failing_check, language_directive
from agents.base import BaseAgent
from agents.tutor.models import TutorInput, TutorResponse
from i18n import Locale, t

logger = logging.getLogger(__name__)


class TutorAgent(BaseAgent):
    """Answers questions with MCP context via LLM."""

    def system_prompt(self, locale: Locale) -> str:
        """Mentor's system prompt."""
        return f"{t('prompt.tutor.intervention_system', locale)}\n\n{language_directive(locale)}"

    async def run(self, input_data: TutorInput, model_id: str | None = None) -> TutorResponse:
        """Answer a question with optional MCP context."""
        resolved_model = model_id or self.agents_config.intervention_model
        locale = input_data.locale
        prompt_parts = [t("prompt.tutor.question_prefix", locale, question=input_data.question)]

        if input_data.failing_check:
            prompt_parts.insert(0, format_failing_check(input_data.failing_check, locale))

        if input_data.agent_context:
            prompt_parts.append(input_data.agent_context.to_prompt(locale))

        try:
            result = await self._agent_for(resolved_model, locale).run("\n\n".join(prompt_parts))
            return TutorResponse(answer=result.output, follow_up_questions=[], references=[])
        except Exception:
            logger.warning("LLM tutor failed", exc_info=True)
            raise
