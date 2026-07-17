"""Routes requests to agents."""

import logging

from agents.hint.agent import HintAgent
from agents.orchestrator.models import (
    InterventionInput,
    OrchestratorInput,
    OrchestratorResponse,
)
from agents.orchestrator.router import resolve_agent
from agents.registry import AGENT_REGISTRY
from config.config_model import ConfigModel
from core.llm.client import resolve_model

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrator creates agents and routes requests."""

    def __init__(self, config: ConfigModel, mcp_client=None, db=None):
        """Stores config and dependencies; agent cache is created lazily."""
        self.config = config
        self._mcp_client = mcp_client
        self._db = db
        self._agents = {}

    def _get_agent(self, agent_name: str):
        """Lazily create an agent by name via AGENT_REGISTRY."""
        if agent_name in self._agents:
            return self._agents[agent_name]

        entry = AGENT_REGISTRY.get(agent_name)
        if entry is None:
            return None
        agent_cls, _ = entry

        # Agent constructors differ in dependencies, handle explicitly.
        if agent_cls is HintAgent:
            agent = agent_cls(self.config)
        else:
            agent = agent_cls(self.config, self._mcp_client)

        self._agents[agent_name] = agent
        return agent

    # LLM agents that accept model_id
    _LLM_AGENTS = frozenset({"tutor", "hint"})

    def _resolve_intervention_model(self, context: dict) -> str:
        """Config's default model, or the session's own choice when follow_session is on."""
        cfg = self.config.agents
        sid = context.get("session_model_id")
        if cfg.interventions_follow_session and sid and cfg.get_entry(sid) is not None:
            return sid
        return cfg.intervention_model

    async def intervene(self, input_data: InterventionInput) -> OrchestratorResponse:
        """Proactive intervention from SessionMonitor."""
        agent_name = f"intervene_{input_data.intervention_type}"
        # single-agent mode (ablation) forces one generalist instead of type-based specialization
        if self.config.learning_analytics.single_agent_mode:
            agent_name = "intervene_tutor"
        resolved_agent_name = resolve_agent(agent_name)

        if resolved_agent_name is None:
            logger.warning("No agent route for intervention: %s", agent_name)
            return OrchestratorResponse(
                agent_used=agent_name,
                success=False,
                error=f"No route for intervention: {agent_name}",
            )

        agent = self._get_agent(resolved_agent_name)
        if agent is None:
            return OrchestratorResponse(
                agent_used=resolved_agent_name,
                success=False,
                error=f"Agent not available for intervention: {resolved_agent_name}",
            )

        try:
            agent_input = self._build_agent_input(
                resolved_agent_name,
                OrchestratorInput(
                    session_id=input_data.session_id,
                    user_id=input_data.user_id,
                    intent=agent_name,
                    payload=input_data.context,
                ),
            )
            if resolved_agent_name in self._LLM_AGENTS:
                model_id = self._resolve_intervention_model(input_data.context)
                result = await agent.run(agent_input, model_id)
                try:
                    creds, _ = resolve_model(model_id)
                    llm_meta = {"model": model_id, "provider": creds.provider.value}
                except Exception:
                    llm_meta = {"model": model_id}
                return OrchestratorResponse(
                    agent_used=resolved_agent_name,
                    success=True,
                    data=result.model_dump(),
                    metadata=llm_meta,
                )
            else:
                result = await agent.run(agent_input)
            return OrchestratorResponse(
                agent_used=resolved_agent_name,
                success=True,
                data=result.model_dump(),
            )
        except Exception as e:
            return OrchestratorResponse(
                agent_used=resolved_agent_name,
                success=False,
                error=str(e),
            )

    def _build_agent_input(self, agent_name: str, input_data: OrchestratorInput):
        """Build input for a specific agent from the payload."""
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
