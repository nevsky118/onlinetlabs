"""HintAgent — агент прогрессивных подсказок с LLM."""

import logging

from agents._shared import format_failing_check
from agents.base import BaseAgent
from agents.hint.models import HintInput, HintResponse
from agents.hint.tools import HintTools
from config.config_model import ConfigModel

logger = logging.getLogger(__name__)


HINT_SYSTEM_PROMPT = (
    "Ты — HintAgent, помощник для выдачи подсказок студентам в лаборатории GNS3.\n\n"
    "Уровни подсказок:\n"
    "- Уровень 1: ОБЩЕЕ направление. Не упоминай команды или интерфейсы.\n"
    "- Уровень 2: ОБЛАСТЬ проблемы. Можно упомянуть компонент или протокол, без точной команды.\n"
    "- Уровень 3: КОНКРЕТНЫЙ шаг. Укажи команду или действие.\n\n"
    "Команды узлов VPCS (PC): `ip <адрес>/<маска>` — задать IP (например `ip 192.168.1.11/24`); "
    "`ip <адрес>/<маска> <шлюз>` — IP со шлюзом; `ping <адрес>` — связность; "
    "`show ip` — текущий IP. Не используй Cisco-синтаксис (`ip address ...`) для VPCS.\n\n"
    "Используй уровень, указанный в запросе. Не давай больше деталей, чем позволяет уровень."
)


class HintAgent(BaseAgent):
    """Прогрессивные подсказки через LLM; без контекста — ошибка."""

    def __init__(self, config: ConfigModel):
        """Инициализация с конфигом."""
        self.tools = HintTools()
        super().__init__(config)

    def system_prompt(self) -> str:
        """Системный промпт с инструкциями по уровням."""
        return HINT_SYSTEM_PROMPT

    async def run(self, input_data: HintInput, model_id: str | None = None) -> HintResponse:
        """Подсказка нужного уровня через LLM. agent_context обязателен."""
        if not input_data.agent_context:
            raise ValueError("hint requires agent_context")

        mid = model_id or self.agents_config.intervention_model
        hint_level = self.tools.get_hint_level(input_data.attempts_count)
        remaining = self.tools.get_remaining_hints(hint_level)

        check_line = ""
        if input_data.failing_check:
            check_line = f"{format_failing_check(input_data.failing_check)}\n"

        try:
            result = await self._agent_for(mid).run(
                f"{check_line}"
                f"Уровень подсказки: {hint_level}\n"
                f"Шаг: {input_data.step_slug}\n"
                f"Последняя ошибка: {input_data.last_error}\n\n"
                f"{input_data.agent_context.to_prompt()}",
            )
            hint_text = result.output
        except Exception:
            logger.warning("LLM hint failed", exc_info=True)
            raise

        return HintResponse(
            hint=hint_text,
            hint_level=hint_level,
            remaining_hints=remaining,
        )
