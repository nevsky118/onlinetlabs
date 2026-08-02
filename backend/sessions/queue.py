"""Redis-backed session queue + active session counters.

Counters per lab (with TTL crash-safety) + global counter + per-lab FIFO queue.
"""

import json
import logging
import time

import redis.asyncio as aioredis
from fastapi import Request

from config import settings

logger = logging.getLogger(__name__)

LAB_CAPS = {
    "lan-static-ip": 100,
    "dhcp-basics": 60,
    "inter-subnet-routing": 40,
}
GLOBAL_CAP = 50
ACTIVE_TTL = 7 * 24 * 3600  # 7d crash-safety on counters
# Average provisioning duration of one session, used for the queue ETA.
QUEUE_AVG_PROVISION_SEC = 30

# Atomic slot acquisition. A GET/INCR pair leaks quota under load: another
# request slips between read and increment. Lua is atomic, so both counters
# move together or the request is rejected.
LUA_TRY_ACQUIRE = """
local lab_key = KEYS[1]
local total_key = KEYS[2]
local lab_cap = tonumber(ARGV[1])
local global_cap = tonumber(ARGV[2])
local ttl = tonumber(ARGV[3])

local curr_lab = tonumber(redis.call('GET', lab_key) or '0')
local curr_total = tonumber(redis.call('GET', total_key) or '0')

if curr_lab >= lab_cap or curr_total >= global_cap then
    return 0
end

redis.call('INCR', lab_key)
redis.call('EXPIRE', lab_key, ttl)
redis.call('INCR', total_key)
redis.call('EXPIRE', total_key, ttl)
return 1
"""

# Decrement both counters, never below zero.
LUA_RELEASE = """
local lab_key = KEYS[1]
local total_key = KEYS[2]

if tonumber(redis.call('GET', lab_key) or '0') > 0 then
    redis.call('DECR', lab_key)
end
if tonumber(redis.call('GET', total_key) or '0') > 0 then
    redis.call('DECR', total_key)
end
return 1
"""


class SessionQueueService:
    """Session queue and active session counters on top of Redis.

    Atomically acquires and releases slots against per-lab and global limits,
    and maintains a FIFO queue of waiters per lab.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        """Creates a Redis client from the given URL or settings."""
        self._redis = aioredis.from_url(redis_url or settings.redis.url, decode_responses=True)

    def _active_key(self, lab_slug: str) -> str:
        """Redis key for the lab's active session counter."""
        return f"active_sessions:{lab_slug}"

    def _queue_key(self, lab_slug: str) -> str:
        """Redis key for the lab's queue of waiters."""
        return f"queue:{lab_slug}"

    def _total_key(self) -> str:
        """Redis key for the global active session counter."""
        return "active_sessions_total"

    async def try_acquire(self, user_id: str, lab_slug: str) -> bool:
        """Tries to atomically acquire a session slot. True if acquired, False otherwise."""
        per_lab_cap = LAB_CAPS.get(lab_slug, GLOBAL_CAP)
        result = await self._redis.eval(
            LUA_TRY_ACQUIRE,
            2,
            self._active_key(lab_slug),
            self._total_key(),
            per_lab_cap,
            GLOBAL_CAP,
            ACTIVE_TTL,
        )
        return int(result) == 1

    async def release(self, lab_slug: str) -> None:
        """Releases a slot, decrementing the lab counter and the global one.

        Clamped at zero: a negative counter would stop the caps from bounding anything.
        """
        await self._redis.eval(
            LUA_RELEASE,
            2,
            self._active_key(lab_slug),
            self._total_key(),
        )

    async def enqueue(self, user_id: str, lab_slug: str) -> int:
        """Appends the user to the end of the queue and returns its length."""
        await self._redis.rpush(
            self._queue_key(lab_slug),
            json.dumps({"user_id": user_id, "ts": int(time.time())}),
        )
        return await self._redis.llen(self._queue_key(lab_slug))

    async def position(self, user_id: str, lab_slug: str) -> int | None:
        """Returns the user's 1-based position in the queue, or None if absent."""
        items = await self._redis.lrange(self._queue_key(lab_slug), 0, -1)
        for i, raw in enumerate(items):
            if json.loads(raw)["user_id"] == user_id:
                return i + 1
        return None

    async def queue_depth(self, lab_slug: str) -> int:
        """Returns the current number of waiters in the lab's queue."""
        return await self._redis.llen(self._queue_key(lab_slug))


# lifespan puts the service on app.state.session_queue; get_queue_service reads it
# from the Request. Callers without an app (tests, background tasks) fall back to
# this lazily created singleton.
_queue_singleton: SessionQueueService | None = None


def _get_or_create_singleton() -> SessionQueueService:
    """Lazily creates and returns the module-level queue service singleton."""
    global _queue_singleton
    if _queue_singleton is None:
        _queue_singleton = SessionQueueService()
    return _queue_singleton


def get_queue_service(request: Request) -> SessionQueueService:
    """Returns session_queue from app.state, falling back to the module singleton."""
    existing = getattr(request.app.state, "session_queue", None)
    if existing is not None:
        return existing
    return _get_or_create_singleton()
