# Manage connections to the target system.

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from mcp_sdk.context import SessionContext
from mcp_sdk.errors import MCPServerError

logger = logging.getLogger(__name__)

Key = tuple[str, str]


class BaseConnectionManager(ABC):
    """Connection manager for the target system."""

    @abstractmethod
    async def connect(self, ctx: SessionContext) -> Any: ...
    @abstractmethod
    async def disconnect(self, connection: Any) -> None: ...
    @abstractmethod
    async def health_check(self, connection: Any) -> bool: ...


@dataclass
class _Entry:
    conn: Any
    last_used: float
    last_checked: float


class ConnectionPool:
    """LRU pool of connections per-(environment_url, user_id).

    `max_size` limits SIMULTANEOUSLY alive connections, not the total number of
    served users: connections idle longer than `idle_ttl` are closed, and when
    space is short the least-recently-used one is evicted (LRU). Without this the
    pool would permanently stop handing out connections after `max_size` unique
    users, since connections were never released until the process stopped.

    A cached connection is checked via `health_check` no more often than
    `health_check_interval`; a dead one is reopened. Only a connection unused
    longer than `min_evict_idle` gets evicted: a live one must not be torn down,
    so if ALL connections are "hot" that's genuine backpressure, and the call
    fails (the caller retries).

    Concurrent requests from the same user are serialized by a per-key lock, so
    no duplicate connections occur.
    """

    def __init__(
        self,
        manager: BaseConnectionManager,
        max_size: int = 50,
        idle_ttl: float = 600.0,
        health_check_interval: float = 60.0,
        min_evict_idle: float = 30.0,
    ) -> None:
        self._manager = manager
        self._max_size = max_size
        self._idle_ttl = idle_ttl
        self._health_check_interval = health_check_interval
        self._min_evict_idle = min_evict_idle
        self._entries: OrderedDict[Key, _Entry] = OrderedDict()
        self._key_locks: dict[Key, asyncio.Lock] = {}
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._entries = OrderedDict()
        self._key_locks = {}

    @property
    def size(self) -> int:
        """Number of live connections in the pool (metrics/tests)."""
        return len(self._entries)

    def _key(self, ctx: SessionContext) -> Key:
        """Pool key: (environment_url, user_id)."""
        return (ctx.environment_url, ctx.user_id)

    def _key_lock(self, key: Key) -> asyncio.Lock:
        lock = self._key_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._key_locks[key] = lock
        return lock

    async def get_connection(self, ctx: SessionContext) -> Any:
        key = self._key(ctx)
        # Lock order is always key → global, otherwise a deadlock is possible.
        async with self._key_lock(key):
            now = time.monotonic()
            await self._drop_idle(now)

            async with self._lock:
                entry = self._entries.get(key)
            if entry is not None:
                if await self._is_alive(entry, now):
                    async with self._lock:
                        entry.last_used = now
                        if key in self._entries:
                            self._entries.move_to_end(key)
                    return entry.conn
                await self._close(key)  # dead → reopen below

            await self._make_room(now)
            conn = await self._manager.connect(ctx)  # network call, kept outside the global lock
            async with self._lock:
                self._entries[key] = _Entry(conn=conn, last_used=now, last_checked=now)
                self._entries.move_to_end(key)
            return conn

    async def release(self, ctx: SessionContext) -> None:
        """Explicitly release a user's connection (e.g. on session end)."""
        key = self._key(ctx)
        async with self._key_lock(key):
            await self._close(key)

    async def close(self) -> None:
        async with self._lock:
            keys = list(self._entries.keys())
        for key in keys:
            await self._close(key)
        async with self._lock:
            self._entries.clear()
            self._key_locks.clear()

    async def _is_alive(self, entry: _Entry, now: float) -> bool:
        """Health-check no more often than health_check_interval; otherwise trust the connection."""
        if now - entry.last_checked < self._health_check_interval:
            return True
        try:
            alive = await self._manager.health_check(entry.conn)
        except Exception:
            logger.warning("health_check упал → считаем соединение мёртвым", exc_info=True)
            alive = False
        entry.last_checked = now
        return alive

    async def _drop_idle(self, now: float) -> None:
        """Close connections idle longer than idle_ttl. This is what fixes the slot leak."""
        async with self._lock:
            stale = [key for key, e in self._entries.items() if now - e.last_used > self._idle_ttl]
        for key in stale:
            await self._close(key)
        self._prune_locks()

    async def _make_room(self, now: float) -> None:
        """Free a slot for a new connection: evict LRU if it isn't "hot"."""
        while True:
            async with self._lock:
                if len(self._entries) < self._max_size:
                    return
                key, entry = next(
                    iter(self._entries.items())
                )  # LRU sits at the head of the OrderedDict
                hot = now - entry.last_used < self._min_evict_idle
                size = len(self._entries)
            if hot:
                raise MCPServerError(
                    f"Connection pool exhausted (max_size={self._max_size}): "
                    f"все {size} соединений активны"
                )
            logger.info("pool: вытесняю LRU-соединение %s", key)
            await self._close(key)

    async def _close(self, key: Key) -> None:
        async with self._lock:
            entry = self._entries.pop(key, None)
        if entry is None:
            return
        try:
            await self._manager.disconnect(entry.conn)
        except Exception:
            logger.warning("disconnect упал для %s", key, exc_info=True)

    def _prune_locks(self) -> None:
        """Don't accumulate locks for users whose connections no longer exist."""
        for key, lock in list(self._key_locks.items()):
            if key not in self._entries and not lock.locked():
                del self._key_locks[key]
