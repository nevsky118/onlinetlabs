"""Управляемый шов контура: единая граница observe/act с governance.

Порядок гейтов: classify(default-deny) → consent → isolation(owner-guard) →
open-suppress(плечо, только act) → rate-backstop(cooldown, только act) → audit → вызов.
"""
from datetime import datetime, timezone

from control_interface.audit import record
from control_interface.consent import has_consent
from control_interface.registry import ToolKind, classify
from experiment.control_arm import ControlArm
from sessions.services.query import get_owned_session


class InterfaceDenied(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class ControlInterface:
    def __init__(self, mcp_client, db_factory, config):
        self._mcp = mcp_client
        self._db_factory = db_factory
        self._cfg = config
        # session_id → ts последнего act. ВНУТРИПРОЦЕССНО: backstop ниже закона
        # управления (in-process cooldown монитора), не распределённый гарант.
        # При multi-worker перенести в Redis/БД (известное ограничение, не overclaim).
        self._last_act_ts: dict[str, float] = {}

    async def _audit(self, user_id, session_id, tool, kind, success, error, lab_slug):
        async with self._db_factory() as db:
            await record(db, user_id=user_id, session_id=session_id, tool=tool,
                         kind=kind, success=success, error=error, lab_slug=lab_slug)

    async def observe(self, tool, ctx, arguments, *, user_id, session_id, lab_slug=None):
        # гейт 1: классификация (default-deny)
        if classify(tool) != ToolKind.OBSERVE:
            await self._audit(user_id, session_id, tool, "observe", False, "unclassified", lab_slug)
            raise InterfaceDenied("unclassified")
        async with self._db_factory() as db:
            # гейт 2: изоляция (owner-guard) — раньше согласия: не раскрывать чужую сессию
            if await get_owned_session(db, session_id, user_id) is None:
                await self._audit(user_id, session_id, tool, "observe", False, "isolation", lab_slug)
                raise InterfaceDenied("isolation")
            # гейт 3: согласие
            if not await has_consent(db, user_id, ToolKind.OBSERVE):
                await self._audit(user_id, session_id, tool, "observe", False, "consent", lab_slug)
                raise InterfaceDenied("consent")
        result = await self._mcp._call_tool(tool, arguments)
        await self._audit(user_id, session_id, tool, "observe", True, None, lab_slug)
        return result

    async def act(self, tool, ctx, arguments, *, user_id, session_id, arm: ControlArm, lab_slug=None):
        # гейт 1: классификация (default-deny)
        if classify(tool) != ToolKind.ACT:
            await self._audit(user_id, session_id, tool, "act", False, "unclassified", lab_slug)
            raise InterfaceDenied("unclassified")
        async with self._db_factory() as db:
            # гейт 2: изоляция (owner-guard) — раньше согласия: не раскрывать чужую сессию
            if await get_owned_session(db, session_id, user_id) is None:
                await self._audit(user_id, session_id, tool, "act", False, "isolation", lab_slug)
                raise InterfaceDenied("isolation")
            # гейт 3: согласие
            if not await has_consent(db, user_id, ToolKind.ACT):
                await self._audit(user_id, session_id, tool, "act", False, "consent", lab_slug)
                raise InterfaceDenied("consent")
        # гейт 4: open-suppress (defense-in-depth)
        if arm == ControlArm.OPEN:
            await self._audit(user_id, session_id, tool, "act", False, "open_arm", lab_slug)
            raise InterfaceDenied("open_arm")
        # гейт 5: rate-backstop (cooldown_period из конфига)
        now = datetime.now(timezone.utc).timestamp()
        last = self._last_act_ts.get(session_id)
        if last is not None and now - last < self._cfg.cooldown_period:
            await self._audit(user_id, session_id, tool, "act", False, "rate", lab_slug)
            raise InterfaceDenied("rate")
        result = await self._mcp.execute_action(ctx, arguments.get("action_name"), arguments.get("params", {}))
        self._last_act_ts[session_id] = now
        await self._audit(user_id, session_id, tool, "act", True, None, lab_slug)
        return result
