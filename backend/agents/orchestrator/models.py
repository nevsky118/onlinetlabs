"""Orchestrator models."""

from pydantic import BaseModel, Field


class OrchestratorInput(BaseModel):
    """Incoming request to the orchestrator."""

    session_id: str
    user_id: str
    intent: str = Field(description="Тип запроса: question | validate | hint | lab | analytics")
    payload: dict = Field(default_factory=dict, description="Данные для целевого агента")


class OrchestratorResponse(BaseModel):
    """Orchestrator's response."""

    agent_used: str
    success: bool
    data: dict = Field(default_factory=dict)
    error: str | None = None
    agent_backend: str | None = None
    latency_ms: int | None = None
    metadata: dict = Field(default_factory=dict)


class InterventionInput(BaseModel):
    """Proactive intervention from SessionMonitor."""

    session_id: str
    user_id: str
    intervention_type: str = Field(description="hint | tutor | simplify")
    context: dict = Field(default_factory=dict, description="Struggle context for the agent")
