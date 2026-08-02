"""MCPContextBuilder assembles context from MCP for agent prompts."""

import asyncio
import logging

from pydantic import BaseModel

from i18n import Locale, t

logger = logging.getLogger(__name__)


class AgentContext(BaseModel):
    """Snapshot of environment state for injection into prompts."""

    topology_summary: str
    recent_errors: list[str]
    recent_actions: list[str]
    struggle_type: str | None
    dominant_error: str | None
    features_summary: str

    def to_prompt(self, locale: Locale) -> str:
        """Context to text for the user message."""
        parts = [t("prompt.context.header", locale)]
        if self.topology_summary:
            parts.append(t("prompt.context.topology", locale, value=self.topology_summary))
        if self.recent_actions:
            parts.append(
                t("prompt.context.recent_actions", locale, value=", ".join(self.recent_actions))
            )
        if self.recent_errors:
            parts.append(
                t("prompt.context.recent_errors", locale, value=", ".join(self.recent_errors))
            )
        if self.struggle_type:
            detail = f" — {self.dominant_error}" if self.dominant_error else ""
            parts.append(
                t("prompt.context.struggle", locale, value=f"{self.struggle_type}{detail}")
            )
        if self.features_summary:
            parts.append(t("prompt.context.metrics", locale, value=self.features_summary))
        return "\n".join(parts)


class MCPContextBuilder:
    """Parallel context gathering from MCP for prompts."""

    def __init__(self, mcp_client):
        """Initialize with an MCP client."""
        self._mcp = mcp_client

    async def build(
        self,
        mcp_ctx,
        features,
        struggle_type: str | None,
        dominant_error: str | None,
        locale: Locale,
    ) -> AgentContext:
        """Topology + actions + errors in parallel → AgentContext."""
        components, actions, errors = await asyncio.gather(
            self._safe_list_components(mcp_ctx),
            self._safe_list_actions(mcp_ctx),
            self._safe_list_errors(mcp_ctx),
        )

        topology_summary = self._summarize_topology(components, locale)
        recent_actions = [f"{a.action}({a.component_id or ''})" for a in actions]
        recent_errors = [e.message for e in errors]

        features_summary = ""
        if features:
            features_summary = t(
                "prompt.context.features_summary",
                locale,
                events=features.events_total,
                repeats=features.error_repeat_count,
                entropy=features.action_sequence_entropy,
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
        """Components; empty list on error."""
        try:
            return await self._mcp.list_components(ctx)
        except Exception:
            logger.warning("Failed to fetch components", exc_info=True)
            return []

    async def _safe_list_actions(self, ctx) -> list:
        """Actions; empty list on error."""
        try:
            return await self._mcp.list_user_actions(ctx, limit=10)
        except Exception:
            logger.warning("Failed to fetch actions", exc_info=True)
            return []

    async def _safe_list_errors(self, ctx) -> list:
        """Errors; empty list on error."""
        try:
            return await self._mcp.list_errors(ctx, since=None)
        except Exception:
            logger.warning("Failed to fetch errors", exc_info=True)
            return []

    @staticmethod
    def _summarize_topology(components: list, locale: Locale) -> str:
        """Components → text summary."""
        if not components:
            return ""
        by_status: dict[str, list[str]] = {}
        for component in components:
            status = component.status
            by_status.setdefault(status, []).append(component.name)
        parts = [f"{', '.join(names)} ({status})" for status, names in by_status.items()]
        return t(
            "prompt.context.components_summary",
            locale,
            count=len(components),
            detail="; ".join(parts),
        )
