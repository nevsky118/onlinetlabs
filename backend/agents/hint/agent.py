"""HintAgent — агент прогрессивных подсказок."""

from config.config_model import ConfigModel
from agents.base import BaseAgent
from agents.hint.models import HintInput, HintResponse
from agents.hint.tools import HintTools


class HintAgent(BaseAgent):
    """Агент для выдачи прогрессивных подсказок."""

    def __init__(self, config: ConfigModel):
        self.tools = HintTools()
        super().__init__(config)

    def system_prompt(self) -> str:
        return (
            "Ты — HintAgent, помощник для выдачи подсказок. "
            "Подсказки прогрессивные: уровень 1 — общие направления, "
            "уровень 2 — конкретные области, уровень 3 — прямые указания. "
            "Не давай ответ сразу, помогай думать."
        )

    async def run(self, input_data: HintInput) -> HintResponse:
        """Выдать подсказку нужного уровня."""
        hint_level = self.tools.get_hint_level(input_data.attempts_count)
        remaining = self.tools.get_remaining_hints(hint_level)
        hint = self.tools.generate_hint(
            input_data.step_slug, hint_level, input_data.last_error
        )

        return HintResponse(
            hint=hint,
            hint_level=hint_level,
            remaining_hints=remaining,
        )
