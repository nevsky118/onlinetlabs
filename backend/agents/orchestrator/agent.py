"""Orchestrator — маршрутизация запросов к агентам."""

import logging

from agents.analytics.agent import AnalyticsAgent
from agents.hint.agent import HintAgent
from agents.orchestrator.models import (
    InterventionInput,
    OrchestratorInput,
    OrchestratorResponse,
)
from agents.orchestrator.router import resolve_agent
from agents.registry import AGENT_REGISTRY
from config.config_model import ConfigModel

logger = logging.getLogger(__name__)


class Orchestrator:
    """Оркестратор создаёт агентов и маршрутизирует запросы."""

    def __init__(self, config: ConfigModel, mcp_client=None, db=None):
        """Сохраняет конфиг и зависимости, кэш агентов создаётся лениво."""
        self.config = config
        self._mcp_client = mcp_client
        self._db = db
        self._agents = {}

    def _get_agent(self, agent_name: str):
        """Lazy создание агента по имени через AGENT_REGISTRY."""
        if agent_name in self._agents:
            return self._agents[agent_name]

        entry = AGENT_REGISTRY.get(agent_name)
        if entry is None:
            return None
        agent_cls, _ = entry

        # Конструкторы агентов отличаются зависимостями, разводим явно.
        if agent_cls is HintAgent:
            agent = agent_cls(self.config)
        elif agent_cls is AnalyticsAgent:
            agent = agent_cls(self.config, self._db)
        else:
            agent = agent_cls(self.config, self._mcp_client)

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

    async def intervene(self, input_data: InterventionInput) -> OrchestratorResponse:
        """Проактивная интервенция от SessionMonitor."""
        agent_name = f"intervene_{input_data.intervention_type}"
        resolved = resolve_agent(agent_name)

        if resolved is None:
            logger.warning("No agent route for intervention: %s", agent_name)
            return OrchestratorResponse(
                agent_used=agent_name, success=False,
                error=f"No route for intervention: {agent_name}",
            )

        agent = self._get_agent(resolved)
        if agent is None:
            return OrchestratorResponse(
                agent_used=resolved, success=False,
                error=f"Agent not available for intervention: {resolved}",
            )

        try:
            agent_input = self._build_agent_input(resolved, OrchestratorInput(
                session_id=input_data.session_id,
                user_id=input_data.user_id,
                intent=agent_name,
                payload=input_data.context,
            ))
            result = await agent.run(agent_input)
            return OrchestratorResponse(
                agent_used=resolved, success=True,
                data=result.model_dump(),
            )
        except Exception as e:
            return OrchestratorResponse(
                agent_used=resolved, success=False, error=str(e),
            )

    def _build_agent_input(self, agent_name: str, input_data: OrchestratorInput):
        """Построить input для конкретного агента из payload."""
        entry = AGENT_REGISTRY.get(agent_name)
        if entry is None:
            raise ValueError(f"No input builder for agent: {agent_name}")
        _, input_model = entry
        payload = {
            "session_id": input_data.session_id,
            "user_id": input_data.user_id,
            **input_data.payload,
        }
        return input_model(**payload)
