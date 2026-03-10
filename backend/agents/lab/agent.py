"""LabAgent — агент взаимодействия с лаб-средой."""

from config.config_model import ConfigModel
from agents.base import BaseAgent
from agents.lab.models import LabQueryInput, LabQueryResult
from agents.lab.tools import LabTools


class LabAgent(BaseAgent):
    """Агент для взаимодействия с лабораторной средой через MCP."""

    def __init__(self, config: ConfigModel, mcp_client):
        self.tools = LabTools(mcp_client)
        super().__init__(config)

    def system_prompt(self) -> str:
        return (
            "Ты — LabAgent, агент для взаимодействия с лабораторной средой. "
            "Твоя роль: получать информацию о состоянии среды, выполнять действия, "
            "интерпретировать состояние компонентов. "
            "Отвечай кратко и по делу."
        )

    async def run(self, input_data: LabQueryInput) -> LabQueryResult:
        """Получить состояние среды и интерпретировать."""
        components = await self.tools.get_topology(input_data)
        summary = await self.tools.interpret_state(input_data, components)
        return LabQueryResult(
            success=True,
            summary=summary,
            components=[c.model_dump() for c in components],
        )
