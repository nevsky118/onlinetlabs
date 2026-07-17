"""LabAgent — агент взаимодействия с лаб-средой."""

from agents.base import BaseAgent
from agents.lab.models import LabQueryInput, LabQueryResult
from agents.lab.tools import LabTools
from config.config_model import ConfigModel

LAB_SYSTEM_PROMPT = (
    "Ты — LabAgent, агент для взаимодействия с лабораторной средой. "
    "Твоя роль: получать информацию о состоянии среды, выполнять действия, "
    "интерпретировать состояние компонентов. "
    "Отвечай кратко и по делу."
)


class LabAgent(BaseAgent):
    """Агент для взаимодействия с лабораторной средой через MCP."""

    def __init__(self, config: ConfigModel, mcp_client):
        """Создаёт инструменты лабы поверх MCP-клиента."""
        self.tools = LabTools(mcp_client)
        super().__init__(config)

    def system_prompt(self) -> str:
        """Системный промпт агента."""
        return LAB_SYSTEM_PROMPT

    async def run(self, input_data: LabQueryInput) -> LabQueryResult:
        """Получить состояние среды и интерпретировать."""
        components = await self.tools.get_topology(input_data)
        summary = await self.tools.interpret_state(input_data, components)
        return LabQueryResult(
            success=True,
            summary=summary,
            components=[c.model_dump() for c in components],
        )
