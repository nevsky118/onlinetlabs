"""Модель события активности ИИ-агентов для observability."""

from datetime import datetime, timezone
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
    ANALYSIS_CYCLE = "analysis_cycle"
    STRUGGLE_DETECTED = "struggle_detected"
    COOLDOWN_SKIP = "cooldown_skip"
    AGENT_INVOKED = "agent_invoked"
    CONTEXT_BUILT = "context_built"
    HINT_GENERATED = "hint_generated"
    DISPATCHED = "dispatched"
    ERROR = "error"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


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
    """Событие: классификатор определил затруднение."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.INTERVENTION, kind=ActivityKind.STRUGGLE_DETECTED,
        agent="analytics",
        summary=f"Определено затруднение: {struggle_type} (уверенность {confidence:.2f})",
        detail={"struggle_type": struggle_type, "confidence": confidence, "crossed": crossed},
    )


def event_model_selected(session_id, user_id, *, model_id, provider):
    """Событие: выбрана модель для генерации."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.CHAT, kind=ActivityKind.MODEL_SELECTED,
        summary=f"Выбрана модель: {model_id} ({provider})",
        detail={"model_id": model_id, "provider": provider},
    )


def event_mcp_context_fetched(session_id, user_id, *, component_count, error_count, verdict_summary):
    """Событие: контекст MCP получен."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.CHAT, kind=ActivityKind.MCP_CONTEXT_FETCHED,
        summary=f"Контекст MCP: {component_count} компонентов, ошибок: {error_count}",
        detail={"component_count": component_count, "error_count": error_count, "verdict_summary": verdict_summary},
    )


def event_tool_call(session_id, user_id, *, name, args_preview):
    """Событие: вызов инструмента."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.CHAT, kind=ActivityKind.TOOL_CALL,
        summary=f"Вызов инструмента: {name}",
        detail={"name": name, "args_preview": args_preview},
    )


def event_tool_result(session_id, user_id, *, name, result_preview, success):
    """Событие: результат инструмента."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.CHAT, kind=ActivityKind.TOOL_RESULT,
        summary=f"Результат {name}: {'успех' if success else 'ошибка'}",
        detail={"name": name, "result_preview": result_preview, "success": success},
    )


def event_fallback(session_id, user_id, *, original_model, fallback_model, reason):
    """Событие: переключение на резервную модель."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.CHAT, kind=ActivityKind.FALLBACK,
        summary=f"Фолбэк: {original_model} → {fallback_model} ({reason})",
        detail={"original_model": original_model, "fallback_model": fallback_model, "reason": reason},
    )


def event_response_finished(session_id, user_id, *, model_id, total_tokens, stop_reason):
    """Событие: ответ завершён."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.CHAT, kind=ActivityKind.RESPONSE_FINISHED,
        summary=f"Ответ завершён ({total_tokens} токенов, {stop_reason})",
        detail={"model_id": model_id, "total_tokens": total_tokens, "stop_reason": stop_reason},
    )


def event_analysis_cycle(session_id, user_id, *, cycle_number, events_count):
    """Событие: цикл анализа интервенций."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.INTERVENTION, kind=ActivityKind.ANALYSIS_CYCLE,
        agent="analytics",
        summary=f"Цикл анализа #{cycle_number}: {events_count} событий",
        detail={"cycle_number": cycle_number, "events_count": events_count},
    )


def event_cooldown_skip(session_id, user_id, *, reason, remaining_seconds):
    """Событие: интервенция пропущена из-за cooldown."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.INTERVENTION, kind=ActivityKind.COOLDOWN_SKIP,
        agent="analytics",
        summary=f"Пропуск интервенции: {reason} (осталось {remaining_seconds}c)",
        detail={"reason": reason, "remaining_seconds": remaining_seconds},
    )


def event_agent_invoked(session_id, user_id, *, agent_name, model_id, parameters_preview):
    """Событие: агент вызван."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.INTERVENTION, kind=ActivityKind.AGENT_INVOKED,
        agent=agent_name,
        summary=f"Агент {agent_name}: {model_id}",
        detail={"agent_name": agent_name, "model_id": model_id, "parameters_preview": parameters_preview},
    )


def event_context_built(session_id, user_id, *, context_size, components_included):
    """Событие: контекст построен."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.CHAT, kind=ActivityKind.CONTEXT_BUILT,
        summary=f"Контекст построен: {context_size} символов, {components_included} компонентов",
        detail={"context_size": context_size, "components_included": components_included},
    )


def event_hint_generated(session_id, user_id, *, level, hint_type, model_used):
    """Событие: подсказка сгенерирована."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.INTERVENTION, kind=ActivityKind.HINT_GENERATED,
        agent="tutor",
        summary=f"Подсказка уровня {level} ({hint_type}, модель {model_used})",
        detail={"level": level, "hint_type": hint_type, "model_used": model_used},
    )


def event_dispatched(session_id, user_id, *, intervention_type, target_agent, status):
    """Событие: интервенция отправлена пользователю."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=ActivitySource.INTERVENTION, kind=ActivityKind.DISPATCHED,
        agent=target_agent,
        summary=f"Интервенция отправлена: {intervention_type} ({status})",
        detail={"intervention_type": intervention_type, "target_agent": target_agent, "status": status},
    )


def event_error(session_id, user_id, *, source, error, agent=None):
    """Событие: ошибка обработки."""
    return AgentActivityEvent(
        session_id=session_id, user_id=user_id,
        source=source, kind=ActivityKind.ERROR,
        agent=agent,
        severity="error",
        summary=f"Ошибка: {error}",
        detail={"error": error},
    )
