"""AI agent activity event model for observability."""

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ActivitySource(str, Enum):
    CHAT = "chat"
    INTERVENTION = "intervention"


class ActivityKind(str, Enum):
    MODEL_SELECTED = "model_selected"
    MCP_CONTEXT_FETCHED = "mcp_context_fetched"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FALLBACK = "fallback"
    RESPONSE_FINISHED = "response_finished"
    STRUGGLE_DETECTED = "struggle_detected"
    COOLDOWN_SKIP = "cooldown_skip"
    AGENT_INVOKED = "agent_invoked"
    HINT_GENERATED = "hint_generated"
    DISPATCHED = "dispatched"
    ERROR = "error"


def _now() -> datetime:
    return datetime.now(tz=UTC)


class AgentActivityEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    user_id: str
    ts: datetime = Field(default_factory=_now)
    source: ActivitySource
    kind: ActivityKind
    agent: str | None = None
    severity: str = "info"
    summary: str
    detail: dict | None = None


def event_struggle_detected(session_id, user_id, *, struggle_type, confidence, crossed):
    """Event: the classifier detected a struggle."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=ActivitySource.INTERVENTION,
        kind=ActivityKind.STRUGGLE_DETECTED,
        agent="analytics",
        summary=f"Struggle detected: {struggle_type} (confidence {confidence:.2f})",
        detail={"struggle_type": struggle_type, "confidence": confidence, "crossed": crossed},
    )


def event_model_selected(session_id, user_id, *, model_id, provider):
    """Event: a model was selected for generation."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=ActivitySource.CHAT,
        kind=ActivityKind.MODEL_SELECTED,
        summary=f"Model selected: {model_id} ({provider})",
        detail={"model_id": model_id, "provider": provider},
    )


def event_mcp_context_fetched(
    session_id, user_id, *, component_count, error_count, verdict_summary
):
    """Event: MCP context was fetched."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=ActivitySource.CHAT,
        kind=ActivityKind.MCP_CONTEXT_FETCHED,
        summary=f"MCP context: {component_count} components, errors: {error_count}",
        detail={
            "component_count": component_count,
            "error_count": error_count,
            "verdict_summary": verdict_summary,
        },
    )


def event_tool_call(session_id, user_id, *, name, args_preview):
    """Event: tool call."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=ActivitySource.CHAT,
        kind=ActivityKind.TOOL_CALL,
        summary=f"Tool call: {name}",
        detail={"name": name, "args_preview": args_preview},
    )


def event_tool_result(session_id, user_id, *, name, result_preview, success):
    """Event: tool result."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=ActivitySource.CHAT,
        kind=ActivityKind.TOOL_RESULT,
        summary=f"Result {name}: {'success' if success else 'error'}",
        detail={"name": name, "result_preview": result_preview, "success": success},
    )


def event_fallback(session_id, user_id, *, original_model, fallback_model, reason):
    """Event: switched to a fallback model."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=ActivitySource.CHAT,
        kind=ActivityKind.FALLBACK,
        summary=f"Fallback: {original_model} → {fallback_model} ({reason})",
        detail={
            "original_model": original_model,
            "fallback_model": fallback_model,
            "reason": reason,
        },
    )


def event_response_finished(session_id, user_id, *, model_id, total_tokens, stop_reason):
    """Event: response finished."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=ActivitySource.CHAT,
        kind=ActivityKind.RESPONSE_FINISHED,
        summary=f"Response finished ({total_tokens} tokens, {stop_reason})",
        detail={"model_id": model_id, "total_tokens": total_tokens, "stop_reason": stop_reason},
    )


def event_cooldown_skip(session_id, user_id, *, reason, remaining_seconds):
    """Event: intervention skipped due to cooldown."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=ActivitySource.INTERVENTION,
        kind=ActivityKind.COOLDOWN_SKIP,
        agent="analytics",
        summary=f"Intervention skipped: {reason} ({remaining_seconds}s remaining)",
        detail={"reason": reason, "remaining_seconds": remaining_seconds},
    )


def event_agent_invoked(session_id, user_id, *, agent_name, model_id, parameters_preview):
    """Event: agent invoked."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=ActivitySource.INTERVENTION,
        kind=ActivityKind.AGENT_INVOKED,
        agent=agent_name,
        summary=f"Agent {agent_name}: {model_id}",
        detail={
            "agent_name": agent_name,
            "model_id": model_id,
            "parameters_preview": parameters_preview,
        },
    )


def event_hint_generated(session_id, user_id, *, level, hint_type, model_used):
    """Event: hint generated."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=ActivitySource.INTERVENTION,
        kind=ActivityKind.HINT_GENERATED,
        agent="tutor",
        summary=f"Hint level {level} ({hint_type}, model {model_used})",
        detail={"level": level, "hint_type": hint_type, "model_used": model_used},
    )


def event_dispatched(session_id, user_id, *, intervention_type, target_agent, status):
    """Event: intervention dispatched to the user."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=ActivitySource.INTERVENTION,
        kind=ActivityKind.DISPATCHED,
        agent=target_agent,
        summary=f"Intervention dispatched: {intervention_type} ({status})",
        detail={
            "intervention_type": intervention_type,
            "target_agent": target_agent,
            "status": status,
        },
    )


def event_error(session_id, user_id, *, source, error, agent=None):
    """Event: processing error."""
    return AgentActivityEvent(
        session_id=session_id,
        user_id=user_id,
        source=source,
        kind=ActivityKind.ERROR,
        agent=agent,
        severity="error",
        summary=f"Error: {error}",
        detail={"error": error},
    )
