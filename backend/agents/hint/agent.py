"""Progressive hints agent backed by an LLM."""

import logging

from agents._shared import format_failing_check, language_directive
from agents.base import BaseAgent
from agents.hint.schemas import HintInput, HintResponse
from agents.hint.tools import HintTools
from config.config_model import ConfigModel
from i18n import Locale, t

logger = logging.getLogger(__name__)


class HintAgent(BaseAgent):
    """Progressive hints via LLM; raises without context."""

    def __init__(self, config: ConfigModel):
        """Initialize with config."""
        self.tools = HintTools()
        super().__init__(config)

    def system_prompt(self, locale: Locale) -> str:
        """System prompt with level instructions."""
        return f"{t('prompt.hint.system', locale)}\n\n{language_directive(locale)}"

    async def run(self, input_data: HintInput, model_id: str | None = None) -> HintResponse:
        """Hint at the requested level via LLM. agent_context is required."""
        if not input_data.agent_context:
            raise ValueError("hint requires agent_context")

        resolved_model = model_id or self.agents_config.intervention_model
        locale = input_data.locale
        hint_level = self.tools.get_hint_level(input_data.attempts_count)
        remaining = self.tools.get_remaining_hints(hint_level)

        lines = []
        if input_data.failing_check:
            lines.append(format_failing_check(input_data.failing_check, locale))
        lines.append(t("prompt.hint.level_line", locale, level=hint_level))
        lines.append(t("prompt.hint.step_line", locale, step=input_data.step_slug))
        lines.append(t("prompt.hint.last_error_line", locale, error=input_data.last_error))
        lines.append("")
        lines.append(input_data.agent_context.to_prompt(locale))

        try:
            result = await self._agent_for(resolved_model, locale).run("\n".join(lines))
            hint_text = result.output
        except Exception:
            logger.warning("LLM hint failed", exc_info=True)
            raise

        return HintResponse(hint=hint_text, hint_level=hint_level, remaining_hints=remaining)
