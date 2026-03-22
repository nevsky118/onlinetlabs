"""HintAgent — агент прогрессивных подсказок с LLM."""

import logging

from config.config_model import ConfigModel
from agents.base import BaseAgent
from agents.hint.models import HintInput, HintResponse
from agents.hint.tools import HintTools

logger = logging.getLogger(__name__)


HINT_SYSTEM_PROMPT = (
    "Ты — HintAgent, помощник для выдачи подсказок студентам.\n\n"
    "Уровни подсказок:\n"
    "- Уровень 1: ОБЩЕЕ направление. Не упоминай команды или интерфейсы.\n"
    "- Уровень 2: ОБЛАСТЬ проблемы. Можно упомянуть компонент или протокол, без точной команды.\n"
    "- Уровень 3: КОНКРЕТНЫЙ шаг. Укажи команду или действие.\n\n"
    "Используй уровень, указанный в запросе. Не давай больше деталей, чем позволяет уровень."
)


class HintAgent(BaseAgent):
    """Прогрессивные подсказки: шаблон без контекста, LLM с контекстом."""

    def __init__(self, config: ConfigModel):
        """Инициализация с конфигом."""
        self.tools = HintTools()
        super().__init__(config)

    def system_prompt(self) -> str:
        """Системный промпт с инструкциями по уровням."""
        return HINT_SYSTEM_PROMPT

    async def run(self, input_data: HintInput) -> HintResponse:
        """Подсказка нужного уровня. LLM при наличии контекста, шаблон без."""
        hint_level = self.tools.get_hint_level(input_data.attempts_count)
        remaining = self.tools.get_remaining_hints(hint_level)

        if input_data.agent_context:
            try:
                result = await self.agent.run(
                    f"Уровень подсказки: {hint_level}\n"
                    f"Шаг: {input_data.step_slug}\n"
                    f"Последняя ошибка: {input_data.last_error}\n\n"
                    f"{input_data.agent_context.to_prompt()}",
                )
                hint_text = result.output
            except Exception:
                logger.warning("LLM недоступен, fallback на шаблон", exc_info=True)
                hint_text = self.tools.generate_hint(
                    input_data.step_slug, hint_level, input_data.last_error
                )
        else:
            hint_text = self.tools.generate_hint(
                input_data.step_slug, hint_level, input_data.last_error
            )

        return HintResponse(
            hint=hint_text,
            hint_level=hint_level,
            remaining_hints=remaining,
        )
