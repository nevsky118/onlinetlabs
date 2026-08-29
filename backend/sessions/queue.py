"""Redis-backed session queue + active session counters.

Counters per lab (with TTL crash-safety) + global counter + per-lab FIFO queue.
"""

import logging

import redis.asyncio as aioredis
from fastapi import Request

from config import settings
from kit.redis import redis_client

logger = logging.getLogger(__name__)

ACTIVE_TTL = 7 * 24 * 3600  # 7d crash-safety on counters
# Fallback ETA before any provisioning has been timed.
QUEUE_AVG_PROVISION_SEC = 30
# Rolling window the ETA is averaged over.
_PROVISION_SAMPLES = 20

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

# Enqueue only if absent. A client polling every few seconds would otherwise
# append a duplicate per poll, growing the list without bound and making both
# position and depth meaningless.
LUA_ENQUEUE = """
local key = KEYS[1]
local user = ARGV[1]
local ttl = tonumber(ARGV[2])

local items = redis.call('LRANGE', key, 0, -1)
for i, v in ipairs(items) do
    if v == user then
        redis.call('EXPIRE', key, ttl)
        return i
    end
end
redis.call('RPUSH', key, user)
redis.call('EXPIRE', key, ttl)
return redis.call('LLEN', key)
"""


class SessionQueueService:
    """Session queue and active session counters on top of Redis.

    Atomically acquires and releases slots against per-lab and global limits,
    and maintains a FIFO queue of waiters per lab.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        """Creates a Redis client from the given URL or settings."""
        self._redis = (
            aioredis.from_url(redis_url, decode_responses=True) if redis_url else redis_client()
        )

    def _active_key(self, lab_slug: str) -> str:
        """Redis key for the lab's active session counter."""
        return f"active_sessions:{lab_slug}"

    def _queue_key(self, lab_slug: str) -> str:
        """Redis key for the lab's queue of waiters."""
        return f"queue:{lab_slug}"

    def _total_key(self) -> str:
        """Redis key for the global active session counter."""
        return "active_sessions_total"

    def _provision_key(self) -> str:
        """Redis key for the rolling provisioning-duration samples."""
        return "provision_seconds"

    def _caps(self, lab_slug: str) -> tuple[int, int]:
        """The lab cap and the global cap, both read from settings."""
        capacity = settings.capacity
        return capacity.per_lab_caps.get(lab_slug, capacity.global_cap), capacity.global_cap

    async def try_acquire(self, user_id: str, lab_slug: str) -> bool:
        """Tries to atomically acquire a session slot. True if acquired, False otherwise."""
        per_lab_cap, global_cap = self._caps(lab_slug)
        result = await self._redis.eval(
            LUA_TRY_ACQUIRE,
            2,
            self._active_key(lab_slug),
            self._total_key(),
            per_lab_cap,
            global_cap,
            ACTIVE_TTL,
        )
        acquired = int(result) == 1
        if acquired:
            await self.dequeue(user_id, lab_slug)
        return acquired

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
        """Puts the user in the queue once and returns their 1-based position."""
        position = await self._redis.eval(
            LUA_ENQUEUE,
            1,
            self._queue_key(lab_slug),
            user_id,
            settings.capacity.queue_ttl_seconds,
        )
        return int(position)

    async def dequeue(self, user_id: str, lab_slug: str) -> int:
        """Removes the user from the queue. Returns how many entries were dropped."""
        removed = await self._redis.lrem(self._queue_key(lab_slug), 0, user_id)
        return int(removed or 0)

    async def position(self, user_id: str, lab_slug: str) -> int | None:
        """Returns the user's 1-based position in the queue, or None if absent."""
        items = await self._redis.lrange(self._queue_key(lab_slug), 0, -1)
        for i, raw in enumerate(items):
            if raw == user_id:
                return i + 1
        return None

    async def queue_depth(self, lab_slug: str) -> int:
        """Returns the current number of waiters in the lab's queue."""
        return await self._redis.llen(self._queue_key(lab_slug))

    async def record_provision_seconds(self, seconds: float) -> None:
        """Adds one observed provisioning duration to the rolling window."""
        key = self._provision_key()
        pipe = self._redis.pipeline()
        pipe.lpush(key, seconds)
        pipe.ltrim(key, 0, _PROVISION_SAMPLES - 1)
        pipe.expire(key, ACTIVE_TTL)
        await pipe.execute()

    async def avg_provision_seconds(self) -> float:
        """Mean observed provisioning duration, or the fallback before any sample."""
        raw = await self._redis.lrange(self._provision_key(), 0, -1)
        values = [float(v) for v in raw if v]
        if not values:
            return float(QUEUE_AVG_PROVISION_SEC)
        return sum(values) / len(values)


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
