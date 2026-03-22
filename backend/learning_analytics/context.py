"""MCPContextBuilder — сборка контекста из MCP для промптов агентов."""

import asyncio
import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentContext(BaseModel):
    """Снимок состояния среды для инжекции в промпты."""

    topology_summary: str
    recent_errors: list[str]
    recent_actions: list[str]
    struggle_type: str | None
    dominant_error: str | None
    features_summary: str

    def to_prompt(self) -> str:
        """Контекст → текст для user message."""
        parts = ["=== СОСТОЯНИЕ СРЕДЫ ==="]
        if self.topology_summary:
            parts.append(f"Топология: {self.topology_summary}")
        if self.recent_actions:
            parts.append(f"Последние действия: {', '.join(self.recent_actions)}")
        if self.recent_errors:
            parts.append(f"Недавние ошибки: {', '.join(self.recent_errors)}")
        if self.struggle_type:
            error_detail = f" — {self.dominant_error}" if self.dominant_error else ""
            parts.append(f"Проблема студента: {self.struggle_type}{error_detail}")
        if self.features_summary:
            parts.append(f"Метрики: {self.features_summary}")
        return "\n".join(parts)


class MCPContextBuilder:
    """Параллельный сбор контекста из MCP для промптов."""

    def __init__(self, mcp_client):
        """Инициализация с MCP-клиентом."""
        self._mcp = mcp_client

    async def build(
        self, mcp_ctx, features, struggle_type: str | None, dominant_error: str | None,
    ) -> AgentContext:
        """Топология + действия + ошибки параллельно → AgentContext."""
        components, actions, errors = await asyncio.gather(
            self._safe_list_components(mcp_ctx),
            self._safe_list_actions(mcp_ctx),
            self._safe_list_errors(mcp_ctx),
        )

        topology_summary = self._summarize_topology(components)
        recent_actions = [f"{a.action}({a.component_id or ''})" for a in actions]
        recent_errors = [e.message for e in errors]

        features_summary = ""
        if features:
            features_summary = (
                f"{features.events_total} событий, "
                f"{features.error_repeat_count} повторов ошибки, "
                f"энтропия {features.action_sequence_entropy}"
            )

        return AgentContext(
            topology_summary=topology_summary,
            recent_errors=recent_errors,
            recent_actions=recent_actions,
            struggle_type=struggle_type,
            dominant_error=dominant_error,
            features_summary=features_summary,
        )

    async def _safe_list_components(self, ctx) -> list:
        """Компоненты; при ошибке — пустой список."""
        try:
            return await self._mcp.list_components(ctx)
        except Exception:
            logger.warning("Не удалось получить компоненты", exc_info=True)
            return []

    async def _safe_list_actions(self, ctx) -> list:
        """Действия; при ошибке — пустой список."""
        try:
            return await self._mcp.list_user_actions(ctx, limit=10)
        except Exception:
            logger.warning("Не удалось получить действия", exc_info=True)
            return []

    async def _safe_list_errors(self, ctx) -> list:
        """Ошибки; при ошибке — пустой список."""
        try:
            return await self._mcp.list_errors(ctx, since=None)
        except Exception:
            logger.warning("Не удалось получить ошибки", exc_info=True)
            return []

    @staticmethod
    def _summarize_topology(components: list) -> str:
        """Компоненты → текстовое резюме."""
        if not components:
            return ""
        by_status: dict[str, list[str]] = {}
        for component in components:
            status = component.status
            by_status.setdefault(status, []).append(component.name)
        parts = [f"{', '.join(names)} ({status})" for status, names in by_status.items()]
        return f"{len(components)} компонентов: {'; '.join(parts)}"
