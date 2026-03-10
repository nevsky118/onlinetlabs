"""Orchestrator — маршрутизация запросов к агентам."""

from config.config_model import ConfigModel
from agents.orchestrator.models import OrchestratorInput, OrchestratorResponse
from agents.orchestrator.router import resolve_agent


class Orchestrator:
    """Оркестратор: создаёт агентов и маршрутизирует запросы."""

    def __init__(self, config: ConfigModel, mcp_client=None, db=None):
        self.config = config
        self._mcp_client = mcp_client
        self._db = db
        self._agents = {}

    def _get_agent(self, agent_name: str):
        """Lazy-инициализация агента по имени."""
        if agent_name in self._agents:
            return self._agents[agent_name]

        if agent_name == "tutor":
            from agents.tutor.agent import TutorAgent
            agent = TutorAgent(self.config, self._mcp_client)
        elif agent_name == "hint":
            from agents.hint.agent import HintAgent
            agent = HintAgent(self.config)
        elif agent_name == "lab":
            from agents.lab.agent import LabAgent
            agent = LabAgent(self.config, self._mcp_client)
        elif agent_name == "validator":
            from agents.validator.agent import ValidatorAgent
            agent = ValidatorAgent(self.config, self._mcp_client)
        elif agent_name == "analytics":
            from agents.analytics.agent import AnalyticsAgent
            agent = AnalyticsAgent(self.config, self._db)
        else:
            return None

        self._agents[agent_name] = agent
        return agent

    async def run(self, input_data: OrchestratorInput) -> OrchestratorResponse:
        """Маршрутизировать запрос к нужному агенту."""
        agent_name = resolve_agent(input_data.intent)

        if agent_name is None:
            return OrchestratorResponse(
                agent_used="none",
                success=False,
                error=f"Unknown intent: {input_data.intent}",
            )

        agent = self._get_agent(agent_name)
        if agent is None:
            return OrchestratorResponse(
                agent_used=agent_name,
                success=False,
                error=f"Agent not available: {agent_name}",
            )

        try:
            # Build agent-specific input from payload
            agent_input = self._build_agent_input(agent_name, input_data)
            result = await agent.run(agent_input)
            return OrchestratorResponse(
                agent_used=agent_name,
                success=True,
                data=result.model_dump(),
            )
        except Exception as e:
            return OrchestratorResponse(
                agent_used=agent_name,
                success=False,
                error=str(e),
            )

    def _build_agent_input(self, agent_name: str, input_data: OrchestratorInput):
        """Построить input для конкретного агента из payload."""
        payload = {
            "session_id": input_data.session_id,
            "user_id": input_data.user_id,
            **input_data.payload,
        }

        if agent_name == "tutor":
            from agents.tutor.models import TutorInput
            return TutorInput(**payload)
        elif agent_name == "hint":
            from agents.hint.models import HintInput
            return HintInput(**payload)
        elif agent_name == "lab":
            from agents.lab.models import LabQueryInput
            return LabQueryInput(**payload)
        elif agent_name == "validator":
            from agents.validator.models import ValidationInput
            return ValidationInput(**payload)
        elif agent_name == "analytics":
            from agents.analytics.models import AnalyticsInput
            return AnalyticsInput(**payload)
        else:
            raise ValueError(f"No input builder for agent: {agent_name}")
