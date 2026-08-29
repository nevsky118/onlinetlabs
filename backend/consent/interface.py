"""The loop's governed seam: a single observe/act boundary with governance.

Gate order: classify(default-deny) -> consent -> isolation(owner-guard) ->
open-suppress(arm, act only) -> rate-backstop(cooldown, act only) -> audit -> call.
"""

from datetime import UTC, datetime

from consent.audit import record
from consent.consent import has_consent
from consent.registry import ToolKind, classify
from experiment.assignment import ControlArm
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
        # session_id -> ts of the last act. IN-PROCESS: a backstop below the control
        # law (the monitor's in-process cooldown), not a distributed guarantee.
        # For multi-worker, move to Redis/DB (a known limitation, not overclaimed).
        self._last_act_ts: dict[str, float] = {}

    async def _audit(self, user_id, session_id, tool, kind, success, error, lab_slug):
        async with self._db_factory() as db:
            await record(
                db,
                user_id=user_id,
                session_id=session_id,
                tool=tool,
                kind=kind,
                success=success,
                error=error,
                lab_slug=lab_slug,
            )

    async def observe(self, tool, ctx, arguments, *, user_id, session_id, lab_slug=None):
        # gate 1: classification (default-deny)
        if classify(tool) != ToolKind.OBSERVE:
            await self._audit(user_id, session_id, tool, "observe", False, "unclassified", lab_slug)
            raise InterfaceDenied("unclassified")
        async with self._db_factory() as db:
            # gate 2: isolation (owner-guard) -- before consent: don't leak another user's session
            if await get_owned_session(db, session_id, user_id) is None:
                await self._audit(
                    user_id, session_id, tool, "observe", False, "isolation", lab_slug
                )
                raise InterfaceDenied("isolation")
            # gate 3: consent
            if not await has_consent(db, user_id, ToolKind.OBSERVE):
                await self._audit(user_id, session_id, tool, "observe", False, "consent", lab_slug)
                raise InterfaceDenied("consent")
        # The typed mcp_client wrapper injects ctx and serializes arguments
        # (like act() -> execute_action). A direct _call_tool dropped ctx -> MCP error.
        try:
            result = await getattr(self._mcp, tool)(ctx, **arguments)
        except Exception as exc:
            await self._audit(
                user_id, session_id, tool, "observe", False, type(exc).__name__, lab_slug
            )
            raise
        await self._audit(user_id, session_id, tool, "observe", True, None, lab_slug)
        return result

    async def authorize_act(self, tool, *, user_id, session_id, arm: ControlArm, lab_slug=None):
        """Runs the act gates. Raises InterfaceDenied and audits the denial.

        Split out from act() so callers that do not deliver through MCP -- the
        intervention dispatch -- pass the same gates instead of bypassing them.
        """
        # gate 1: classification (default-deny)
        if classify(tool) != ToolKind.ACT:
            await self._audit(user_id, session_id, tool, "act", False, "unclassified", lab_slug)
            raise InterfaceDenied("unclassified")
        async with self._db_factory() as db:
            # gate 2: isolation (owner-guard) -- before consent: don't leak another user's session
            if await get_owned_session(db, session_id, user_id) is None:
                await self._audit(user_id, session_id, tool, "act", False, "isolation", lab_slug)
                raise InterfaceDenied("isolation")
            # gate 3: consent
            if not await has_consent(db, user_id, ToolKind.ACT):
                await self._audit(user_id, session_id, tool, "act", False, "consent", lab_slug)
                raise InterfaceDenied("consent")
        # gate 4: open-suppress (defense-in-depth)
        if arm == ControlArm.OPEN:
            await self._audit(user_id, session_id, tool, "act", False, "open_arm", lab_slug)
            raise InterfaceDenied("open_arm")
        # gate 5: rate-backstop (cooldown_period from config)
        now = datetime.now(UTC).timestamp()
        last = self._last_act_ts.get(session_id)
        if last is not None and now - last < self._cfg.cooldown_period:
            await self._audit(user_id, session_id, tool, "act", False, "rate", lab_slug)
            raise InterfaceDenied("rate")

    async def record_act(self, tool, *, user_id, session_id, success, lab_slug=None):
        """Stamps the rate window and writes the act audit row after a delivered act."""
        self._last_act_ts[session_id] = datetime.now(UTC).timestamp()
        await self._audit(user_id, session_id, tool, "act", success, None, lab_slug)

    async def act(
        self, tool, ctx, arguments, *, user_id, session_id, arm: ControlArm, lab_slug=None
    ):
        await self.authorize_act(
            tool, user_id=user_id, session_id=session_id, arm=arm, lab_slug=lab_slug
        )
        try:
            result = await self._mcp.execute_action(
                ctx, arguments.get("action_name"), arguments.get("params", {})
            )
        except Exception:
            await self.record_act(
                tool, user_id=user_id, session_id=session_id, success=False, lab_slug=lab_slug
            )
            raise
        await self.record_act(
            tool, user_id=user_id, session_id=session_id, success=True, lab_slug=lab_slug
        )
        return result
