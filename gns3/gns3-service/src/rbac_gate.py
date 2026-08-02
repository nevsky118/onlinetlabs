# Serializes writes to GNS3 RBAC (users and ACLs).

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_LOCK_KEY = "lock:gns3_rbac_write"


class RbacGate:
    """Serializes writes into GNS3 RBAC.

    GNS3 returns 500 on concurrent POST /v3/access/acl and retries just collide
    again: at 5 simultaneous students ~60% of sessions failed. User and ACL
    creation go through the gate; duplicate_project does not, since it touches no
    RBAC and should stay parallel.

    asyncio.Lock covers the process, the optional Redis lock covers replicas.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        lock_ttl_seconds: int = 30,
        poll_interval: float = 0.05,
        wait_timeout: float = 60.0,
    ) -> None:
        self._local = asyncio.Lock()
        self._redis = aioredis.from_url(redis_url, decode_responses=True) if redis_url else None
        self._lock_ttl = lock_ttl_seconds
        self._poll_interval = poll_interval
        self._wait_timeout = wait_timeout

    @asynccontextmanager
    async def __call__(self):
        async with self._local:
            token = await self._acquire_distributed()
            try:
                yield
            finally:
                await self._release_distributed(token)

    async def _acquire_distributed(self) -> str | None:
        """Redis lock with TTL (survives a replica crash). None if Redis isn't configured."""
        if self._redis is None:
            return None
        token = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._wait_timeout
        while True:
            try:
                acquired = await self._redis.set(_LOCK_KEY, token, nx=True, ex=self._lock_ttl)
            except Exception:
                # Redis unavailable → don't block provisioning: the local lock is enough
                # for a single replica (current deployment).
                logger.warning(
                    "RBAC gate, Redis unavailable, falling back to the local lock", exc_info=True
                )
                return None
            if acquired:
                return token
            if loop.time() >= deadline:
                logger.warning(
                    "RBAC gate, waited %.0fs for the lock, continuing without it",
                    self._wait_timeout,
                )
                return None
            await asyncio.sleep(self._poll_interval)

    async def _release_distributed(self, token: str | None) -> None:
        """Release the lock only if it's still ours (TTL may have expired and been taken over)."""
        if self._redis is None or token is None:
            return
        try:
            current = await self._redis.get(_LOCK_KEY)
            if current == token:
                await self._redis.delete(_LOCK_KEY)
        except Exception:
            logger.warning("RBAC gate, failed to release the Redis lock", exc_info=True)
