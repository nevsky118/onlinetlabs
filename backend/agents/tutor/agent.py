"""TutorAgent — агент-наставник для ответов на вопросы."""

import logging

from agents._shared import format_failing_check
from agents.base import BaseAgent
from agents.tutor.models import TutorInput, TutorResponse
from agents.tutor.tools import TutorTools
from config.config_model import ConfigModel

logger = logging.getLogger(__name__)


TUTOR_SYSTEM_PROMPT = (
    "Ты — TutorAgent, наставник для студентов, изучающих сетевые технологии.\n"
    "Правила:\n"
    "- Объясняй концепции, не давай готовых решений\n"
    "- Используй контекст среды для конкретных объяснений\n"
    "- Если студент повторяет ошибку, объясни почему она возникает\n"
    "- Предложи 1-2 вопроса для самопроверки\n"
    "- Отвечай кратко (3-5 предложений)"
)


class TutorAgent(BaseAgent):
    """Отвечает на вопросы с MCP-контекстом через LLM."""

    def __init__(self, config: ConfigModel, mcp_client=None):
        """Инициализация с конфигом и MCP-клиентом."""
        self.tools = TutorTools(mcp_client)
        super().__init__(config)

    def system_prompt(self) -> str:
        """Системный промпт наставника."""
        return TUTOR_SYSTEM_PROMPT

    async def run(self, input_data: TutorInput, model_id: str | None = None) -> TutorResponse:
        """Ответ на вопрос с опциональным MCP-контекстом."""
        mid = model_id or self.agents_config.intervention_model
        prompt_parts = [f"Вопрос студента: {input_data.question}"]

        if input_data.failing_check:
            prompt_parts.insert(0, format_failing_check(input_data.failing_check))

        if input_data.agent_context:
            prompt_parts.append(input_data.agent_context.to_prompt())

        try:
            result = await self._agent_for(mid).run("\n\n".join(prompt_parts))
            return TutorResponse(
                answer=result.output,
                follow_up_questions=[],
                references=[],
            )
        except Exception:
            logger.warning("LLM tutor failed", exc_info=True)
            raise
