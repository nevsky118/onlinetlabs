"""BehavioralCollector — polling the MCP server and storing behavioral events."""

import asyncio
import hashlib
import logging
from collections import OrderedDict
from datetime import UTC, datetime
from uuid import uuid4

from mcp_sdk.models import ErrorEntry, LogEntry, LogLevel, UserAction

from config.config_model import LearningAnalyticsConfig

logger = logging.getLogger(__name__)


class BehavioralCollector:
    """Periodic MCP polling, normalization, deduplication, DB write."""

    def __init__(self, mcp_client, db_factory, learning_analytics_config: LearningAnalyticsConfig, control_interface=None):
        """Initialize. control_interface is an optional seam (Task 7); None → direct mcp_client calls."""
        self._mcp = mcp_client
        self._db_factory = db_factory
        self._cfg = learning_analytics_config
        self._control_interface = control_interface  # seam P1; None = backward-compat fallback
        self._task: asyncio.Task | None = None
        self._running = False
        self._last_error_poll: datetime | None = None
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._component_types: dict[str, str] = {}
        self._session_id: str | None = None
        self._user_id: str | None = None
        self._lab_slug: str | None = None
        self._ctx = None

    @property
    def is_running(self) -> bool:
        """Whether the polling loop is running."""
        return self._running

    async def start(self, session_id: str, user_id: str, lab_slug: str, ctx) -> None:
        """Start the polling loop as an asyncio.Task."""
        self._session_id = session_id
        self._user_id = user_id
        self._lab_slug = lab_slug
        self._ctx = ctx
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Stop the loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    # Polling loop

    async def _poll_loop(self) -> None:
        """Infinite loop: poll → pause → repeat."""
        while self._running:
            try:
                await self._poll_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.warning("Цикл опроса: ошибка", exc_info=True)
            await asyncio.sleep(self._cfg.poll_interval)

    async def _poll_cycle(self) -> None:
        """One cycle: actions + logs + errors → (evidence snapshot) → persist."""
        events: list[dict] = []
        events.extend(await self._fetch_actions())
        events.extend(await self._fetch_logs())
        events.extend(await self._fetch_errors())
        if events:
            if self._cfg.evidence_capture_enabled:
                await self._capture_evidence(events)
            await self._persist(events)

    async def _capture_evidence(self, events: list[dict]) -> None:
        """Raw snapshot of the cycle's MCP observations for annotation (best-effort, disjoint from features)."""
        from learning_analytics.evidence import capture_snapshot
        try:
            async with self._db_factory() as db:
                await capture_snapshot(
                    db, self._session_id, self._user_id, self._lab_slug,
                    kind="mcp_events", payload={"events": events},
                )
        except Exception:
            logger.warning("Не удалось записать evidence-снимок", exc_info=True)

    async def _call_observe(self, tool: str, arguments: dict):
        """Observe via the seam or directly (fallback)."""
        if self._control_interface is not None:
            return await self._control_interface.observe(
                tool, self._ctx, arguments,
                user_id=self._user_id,
                session_id=self._session_id,
                lab_slug=self._lab_slug,
            )
        # fallback: direct mcp_client call
        if tool == "list_user_actions":
            return await self._mcp.list_user_actions(self._ctx, **arguments)
        if tool == "get_logs":
            return await self._mcp.get_logs(self._ctx, **arguments)
        if tool == "list_errors":
            return await self._mcp.list_errors(self._ctx, **arguments)
        raise ValueError(f"Неизвестный observe-инструмент: {tool}")

    async def _fetch_actions(self) -> list[dict]:
        """Fetch UserAction from MCP, deduplicate, normalize."""
        result: list[dict] = []
        try:
            from control_interface.interface import InterfaceDenied
            actions = await self._call_observe(
                "list_user_actions", {"limit": self._cfg.mcp_actions_limit}
            )
            for a in actions:
                key = self._dedup_key(a.timestamp, a.action, a.component_id)
                if self._is_new(key):
                    await self._resolve_type(a.component_id)
                    result.append(self.normalize_user_action(
                        a, self._session_id, self._user_id, self._lab_slug,
                        self._component_types,
                    ))
        except Exception as exc:
            from control_interface.interface import InterfaceDenied
            if isinstance(exc, InterfaceDenied):
                logger.warning("observe list_user_actions отклонён швом: %s", exc.reason)
            else:
                logger.warning("Не удалось получить user actions", exc_info=True)
        return result

    async def _fetch_logs(self) -> list[dict]:
        """Fetch LogEntry from MCP, deduplicate, normalize."""
        result: list[dict] = []
        try:
            logs = await self._call_observe(
                "get_logs", {"level": LogLevel.ALL, "limit": self._cfg.mcp_logs_limit}
            )
            for log in logs:
                key = self._dedup_key(log.timestamp, "log", log.source)
                if self._is_new(key):
                    result.append(self.normalize_log_entry(
                        log, self._session_id, self._user_id, self._lab_slug,
                    ))
        except Exception as exc:
            from control_interface.interface import InterfaceDenied
            if isinstance(exc, InterfaceDenied):
                logger.warning("observe get_logs отклонён швом: %s", exc.reason)
            else:
                logger.warning("Не удалось получить логи", exc_info=True)
        return result

    async def _fetch_errors(self) -> list[dict]:
        """Fetch ErrorEntry from MCP (with since), normalize."""
        result: list[dict] = []
        try:
            errors = await self._call_observe(
                "list_errors", {"since": self._last_error_poll}
            )
            self._last_error_poll = datetime.now(tz=UTC)
            for err in errors:
                result.append(self.normalize_error_entry(
                    err, self._session_id, self._user_id, self._lab_slug,
                ))
        except Exception as exc:
            from control_interface.interface import InterfaceDenied
            if isinstance(exc, InterfaceDenied):
                logger.warning("observe list_errors отклонён швом: %s", exc.reason)
            else:
                logger.warning("Не удалось получить ошибки", exc_info=True)
        return result

    # DB write

    async def _persist(self, events: list[dict]) -> None:
        """Batch write of events to the DB."""
        from models.behavioral_event import BehavioralEvent
        try:
            async with self._db_factory() as session:
                for evt in events:
                    session.add(BehavioralEvent(**evt))
                await session.commit()
        except Exception:
            logger.error("Не удалось сохранить события", exc_info=True)

    # Helpers

    async def _resolve_type(self, component_id: str | None) -> str | None:
        """Lazy resolution of component_type via MCP."""
        if not component_id or component_id in self._component_types:
            return self._component_types.get(component_id)
        try:
            detail = await self._mcp.get_component(self._ctx, component_id)
            self._component_types[component_id] = detail.type
            return detail.type
        except Exception:
            return None

    def _dedup_key(self, ts: datetime, action: str, cid: str | None) -> str:
        """Stable dedup key from timestamp, action, and component_id.

        MD5 for brevity, not security.
        """
        raw = f"{ts.isoformat()}:{action}:{cid or ''}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _is_new(self, key: str) -> bool:
        """True if the event is new. Bounded OrderedDict."""
        if key in self._seen:
            return False
        self._seen[key] = None
        while len(self._seen) > self._cfg.dedup_max_size:
            self._seen.popitem(last=False)  # evict the oldest
        return True

    # Normalization of MCP models → event dict

    @staticmethod
    def normalize_user_action(
        action: UserAction, session_id: str, user_id: str, lab_slug: str,
        component_types: dict[str, str] | None = None,
    ) -> dict:
        """UserAction → dict for BehavioralEvent."""
        return {
            "id": str(uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "lab_slug": lab_slug,
            "timestamp": action.timestamp,
            "event_type": "action",
            "component_id": action.component_id,
            "component_type": (component_types or {}).get(action.component_id),
            "action": action.action,
            "raw_command": action.raw_command,
            "success": action.success,
            "severity": None,
            "message": None,
            "extra_data": None,
        }

    @staticmethod
    def normalize_log_entry(
        log: LogEntry, session_id: str, user_id: str, lab_slug: str,
    ) -> dict:
        """LogEntry → dict for BehavioralEvent."""
        return {
            "id": str(uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "lab_slug": lab_slug,
            "timestamp": log.timestamp,
            "event_type": "log",
            "component_id": log.source,
            "component_type": None,
            "action": f"log_{log.level.value}",
            "raw_command": None,
            "success": True,
            "severity": log.level.value,
            "message": log.message,
            "extra_data": None,
        }

    @staticmethod
    def normalize_error_entry(
        error: ErrorEntry, session_id: str, user_id: str, lab_slug: str,
    ) -> dict:
        """ErrorEntry → dict for BehavioralEvent."""
        return {
            "id": str(uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "lab_slug": lab_slug,
            "timestamp": error.timestamp,
            "event_type": "error",
            "component_id": error.component_id,
            "component_type": None,
            "action": "error",
            "raw_command": None,
            "success": False,
            "severity": error.level.value,
            "message": error.message,
            "extra_data": {"details": error.details} if error.details else None,
        }
