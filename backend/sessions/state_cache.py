"""Redis-backed state cache for /users/me/sessions/{id}/state.

Wraps a redis.asyncio client to store SessionState JSON with a short TTL.
Production safety: corrupted cache entries (e.g. partial writes during eviction)
log and treat as miss instead of crashing the request path.
"""

import json
import logging

logger = logging.getLogger(__name__)


class StateCache:
    """Session state cache in Redis with a short TTL.

    Stores SessionState as JSON. Corrupted entries are treated as a miss,
    not a request error.
    """

    def __init__(self, redis, ttl_seconds: int = 5) -> None:
        """Stores the Redis client and the entry TTL in seconds."""
        self._redis = redis
        self._ttl = ttl_seconds

    @staticmethod
    def _key(session_id: str) -> str:
        """Redis key for the given session's state."""
        return f"session:state:{session_id}"

    async def get(self, session_id: str) -> dict | None:
        """Returns the cached session state, or None on a miss."""
        raw = await self._redis.get(self._key(session_id))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Corrupted state cache entry for %s, treating as miss", session_id)
            return None

    async def set(self, session_id: str, state: dict) -> None:
        """Saves the session state to the cache with the given TTL."""
        await self._redis.set(self._key(session_id), json.dumps(state), ex=self._ttl)

    async def invalidate(self, session_id: str) -> None:
        """Deletes the cached session state."""
        await self._redis.delete(self._key(session_id))
