"""TutorAgent — агент-наставник для ответов на вопросы."""

import logging

from config.config_model import ConfigModel
from agents.base import BaseAgent
from agents.tutor.models import TutorInput, TutorResponse
from agents.tutor.tools import TutorTools

logger = logging.getLogger(__name__)


class TutorAgent(BaseAgent):
    """Отвечает на вопросы с MCP-контекстом через LLM."""

    def __init__(self, config: ConfigModel, mcp_client=None):
        """Инициализация с конфигом и MCP-клиентом."""
        self.tools = TutorTools(mcp_client)
        super().__init__(config)

    def system_prompt(self) -> str:
        """Системный промпт наставника."""
        return (
            "Ты — TutorAgent, наставник для студентов, изучающих сетевые технологии.\n"
            "Правила:\n"
            "- Объясняй концепции, не давай готовых решений\n"
            "- Используй контекст среды для конкретных объяснений\n"
            "- Если студент повторяет ошибку, объясни почему она возникает\n"
            "- Предложи 1-2 вопроса для самопроверки\n"
            "- Отвечай кратко (3-5 предложений)"
        )

    async def run(self, input_data: TutorInput) -> TutorResponse:
        """Ответ на вопрос с опциональным MCP-контекстом."""
        prompt_parts = [f"Вопрос студента: {input_data.question}"]

        if input_data.agent_context:
            prompt_parts.append(input_data.agent_context.to_prompt())

        try:
            result = await self.agent.run("\n\n".join(prompt_parts))
            return TutorResponse(
                answer=result.output,
                follow_up_questions=[],
                references=[],
            )
        except Exception:
            logger.warning("LLM недоступен, fallback на шаблон", exc_info=True)
            context_parts = []
            if input_data.lab_slug:
                context_parts.append(await self.tools.get_lab_context(input_data.lab_slug))
            if input_data.context:
                context_parts.append(input_data.context)
            full_context = "; ".join(context_parts) if context_parts else "Общий вопрос"
            return TutorResponse(
                answer=f"Ответ на вопрос: {input_data.question} (контекст: {full_context})",
                follow_up_questions=["Можешь объяснить подробнее?"],
                references=[],
            )
