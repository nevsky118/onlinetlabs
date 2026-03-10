"""TutorAgent — агент-наставник для ответов на вопросы."""

from config.config_model import ConfigModel
from agents.base import BaseAgent
from agents.tutor.models import TutorInput, TutorResponse
from agents.tutor.tools import TutorTools


class TutorAgent(BaseAgent):
    """Агент-наставник. Отвечает на вопросы студентов."""

    def __init__(self, config: ConfigModel, mcp_client=None):
        self.tools = TutorTools(mcp_client)
        super().__init__(config)

    def system_prompt(self) -> str:
        return (
            "Ты — TutorAgent, наставник для студентов. "
            "Твоя роль: отвечать на вопросы по лабораторным работам, "
            "объяснять концепции, предлагать дополнительные вопросы для самопроверки. "
            "Будь терпелив, объясняй доступно, не давай готовых решений."
        )

    async def run(self, input_data: TutorInput) -> TutorResponse:
        """Обработать вопрос студента."""
        context_parts = []

        if input_data.lab_slug:
            lab_ctx = await self.tools.get_lab_context(input_data.lab_slug)
            context_parts.append(lab_ctx)

        if input_data.lab_slug and input_data.step_slug:
            step_ctx = await self.tools.get_step_context(
                input_data.lab_slug, input_data.step_slug
            )
            context_parts.append(step_ctx)

        if input_data.context:
            context_parts.append(input_data.context)

        full_context = "; ".join(context_parts) if context_parts else "Общий вопрос"

        return TutorResponse(
            answer=f"Ответ на вопрос: {input_data.question} (контекст: {full_context})",
            follow_up_questions=[
                "Можешь объяснить подробнее?",
                "Что будет, если изменить параметры?",
            ],
            references=[],
        )
