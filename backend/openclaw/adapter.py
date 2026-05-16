"""Адаптер OpenClaw для интервенций платформы."""

from agents.hint.tools import HintTools
from agents.orchestrator.models import InterventionInput, OrchestratorResponse
from learning_analytics.context import AgentContext
from openclaw.client import OpenClawClient, OpenClawCompletion


class OpenClawInterventionAdapter:
    """Преобразует вход интервенции платформы в запросы chat completions OpenClaw."""

    def __init__(self, client: OpenClawClient):
        self._client = client
        self._hint_tools = HintTools()

    async def generate(self, input_data: InterventionInput) -> OrchestratorResponse:
        """Сгенерировать нормализованный результат интервенции через OpenClaw."""
        completion = await self._client.complete(self._build_messages(input_data))
        metadata = self._metadata(completion)

        if not completion.success:
            return OrchestratorResponse(
                agent_used="openclaw",
                agent_backend="openclaw",
                success=False,
                error=self._format_error(completion),
                latency_ms=completion.latency_ms,
                metadata=metadata,
            )

        return OrchestratorResponse(
            agent_used="openclaw",
            agent_backend="openclaw",
            success=True,
            data=self._build_data(input_data, completion.content),
            latency_ms=completion.latency_ms,
            metadata=metadata,
        )

    def _build_messages(self, input_data: InterventionInput) -> list[dict]:
        """Собрать OpenAI-совместимые сообщения для OpenClaw Gateway."""
        return [
            {
                "role": "system",
                "content": (
                    "Ты — учебный ассистент OnlineTLabs. "
                    "Дай короткую адаптивную помощь студенту, не раскрывая полное решение. "
                    "Соблюдай указанный тип интервенции."
                ),
            },
            {"role": "user", "content": self._build_user_prompt(input_data)},
        ]

    def _build_user_prompt(self, input_data: InterventionInput) -> str:
        """Собрать детерминированный промпт из нормализованного контекста."""
        context = input_data.context
        parts = [
            f"session_id: {input_data.session_id}",
            f"user_id: {input_data.user_id}",
            f"intervention_type: {input_data.intervention_type}",
            f"lab_slug: {context.get('lab_slug', '')}",
            f"step_slug: {context.get('step_slug', '')}",
            f"struggle_type: {context.get('struggle_type', '')}",
            f"dominant_error: {context.get('dominant_error', '')}",
            f"attempts_count: {context.get('attempts_count', 0)}",
            f"last_error: {context.get('last_error', '')}",
        ]
        agent_context = self._agent_context_prompt(context.get("agent_context"))
        if agent_context:
            parts.append(agent_context)
        return "\n".join(parts)

    def _agent_context_prompt(self, value) -> str:
        """Преобразовать AgentContext или словарь в текст промпта."""
        if value is None:
            return ""
        if hasattr(value, "to_prompt"):
            return value.to_prompt()
        if isinstance(value, dict):
            return AgentContext(**value).to_prompt()
        return str(value)

    def _build_data(self, input_data: InterventionInput, content: str) -> dict:
        """Собрать полезную нагрузку ответа для существующих путей доставки."""
        if input_data.intervention_type == "tutor":
            return {"answer": content}
        hint_level = self._hint_tools.get_hint_level(
            int(input_data.context.get("attempts_count", 0) or 0)
        )
        return {
            "hint": content,
            "hint_level": hint_level,
            "remaining_hints": self._hint_tools.get_remaining_hints(hint_level),
        }

    @staticmethod
    def _metadata(completion: OpenClawCompletion) -> dict:
        """Собрать метаданные трассировки для логирования эксперимента."""
        metadata = {
            "model": completion.model,
            "provider": completion.provider,
            "usage": completion.usage,
        }
        if completion.error_code:
            metadata["error_code"] = completion.error_code
        if completion.error_message:
            metadata["error_message"] = completion.error_message
        return metadata

    @staticmethod
    def _format_error(completion: OpenClawCompletion) -> str:
        """Отформатировать ошибку адаптера без вызова другого бэкенда."""
        if completion.error_code and completion.error_message:
            return f"{completion.error_code}: {completion.error_message}"
        return completion.error_code or completion.error_message or "openclaw_error"
