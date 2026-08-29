"""One-time tickets that replace handing the GNS3 password to the browser."""

import json
import logging
import secrets

import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger(__name__)

TICKET_TTL_SEC = 120
_PREFIX = "gns3ticket:"


def _key(ticket: str) -> str:
    """Redis key for a ticket."""
    return f"{_PREFIX}{ticket}"


class TicketStore:
    """Short-lived single-use tickets in Redis."""

    def __init__(self, redis=None) -> None:
        """Uses the given Redis client or builds one from settings."""
        self._redis = redis or aioredis.from_url(settings.redis.url, decode_responses=True)

    async def issue(self, session_id: str, user_id: str) -> str:
        """Mints a ticket bound to one session and returns it."""
        ticket = secrets.token_urlsafe(32)
        await self._redis.set(
            _key(ticket),
            json.dumps({"session_id": session_id, "user_id": user_id}),
            ex=TICKET_TTL_SEC,
        )
        return ticket

    async def redeem(self, ticket: str) -> dict | None:
        """Consumes a ticket. Returns its payload, or None if unknown or already used."""
        if not ticket:
            return None
        raw = await self._redis.getdel(_key(ticket))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("corrupt ticket payload")
            return None


_store: TicketStore | None = None


def get_ticket_store() -> TicketStore:
    """Lazily creates the module-level ticket store."""
    global _store
    if _store is None:
        _store = TicketStore()
    return _store
