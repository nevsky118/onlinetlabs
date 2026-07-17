# Управление подключениями к целевой системе.

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
    """Менеджер подключений к целевой системе."""

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
    """LRU-пул подключений per-(environment_url, user_id).

    `max_size` ограничивает ОДНОВРЕМЕННО живые соединения, а не общее число
    обслуженных пользователей: простаивающие дольше `idle_ttl` закрываются, а при
    нехватке места вытесняется давно не используемое (LRU). Без этого пул после
    `max_size` уникальных пользователей навсегда переставал выдавать соединения —
    соединения не освобождались до остановки процесса.

    Соединение из кеша проверяется `health_check` не чаще `health_check_interval`;
    мёртвое — переоткрывается. Вытесняется только соединение, не использовавшееся
    дольше `min_evict_idle`: рвать живое нельзя, поэтому если ВСЕ соединения
    «горячие» — это настоящий backpressure, и вызов падает (вызывающий повторит).

    Параллельные запросы одного пользователя сериализуются per-key локом, поэтому
    дублирующих подключений не возникает.
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
        """Число живых соединений в пуле (метрики/тесты)."""
        return len(self._entries)

    def _key(self, ctx: SessionContext) -> Key:
        """Ключ пула: (environment_url, user_id)."""
        return (ctx.environment_url, ctx.user_id)

    def _key_lock(self, key: Key) -> asyncio.Lock:
        lock = self._key_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._key_locks[key] = lock
        return lock

    async def get_connection(self, ctx: SessionContext) -> Any:
        key = self._key(ctx)
        # Порядок локов всегда key → global, иначе возможен дедлок.
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
                await self._close(key)  # мёртвое → переоткрываем ниже

            await self._make_room(now)
            conn = await self._manager.connect(ctx)  # сеть — вне глобального лока
            async with self._lock:
                self._entries[key] = _Entry(conn=conn, last_used=now, last_checked=now)
                self._entries.move_to_end(key)
            return conn

    async def release(self, ctx: SessionContext) -> None:
        """Явно освободить соединение пользователя (например, при завершении сессии)."""
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
        """Health-check не чаще health_check_interval — иначе доверяем соединению."""
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
        """Закрыть простаивающие дольше idle_ttl — это и лечит утечку слотов."""
        async with self._lock:
            stale = [key for key, e in self._entries.items() if now - e.last_used > self._idle_ttl]
        for key in stale:
            await self._close(key)
        self._prune_locks()

    async def _make_room(self, now: float) -> None:
        """Освободить слот под новое: вытеснить LRU, если оно не «горячее»."""
        while True:
            async with self._lock:
                if len(self._entries) < self._max_size:
                    return
                key, entry = next(iter(self._entries.items()))  # LRU — голова OrderedDict
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
        """Не копить локи пользователей, чьих соединений уже нет."""
        for key, lock in list(self._key_locks.items()):
            if key not in self._entries and not lock.locked():
                del self._key_locks[key]
