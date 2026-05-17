# In-memory кеш state-снапшотов сессий с TTL.
#
# Назначение: схлопнуть burst-запросы от UI/WS, не дёргая GNS3 на каждый рендер.

from __future__ import annotations

import time
from typing import Generic, TypeVar

T = TypeVar("T")


class StateCache(Generic[T]):
    """Простой TTL-кеш по ключу сессии.

    Не потокобезопасен в строгом смысле, но в одном event loop этого достаточно.
    """

    def __init__(self, ttl_seconds: float = 5.0) -> None:
        self._ttl = ttl_seconds
        self._data: dict[str, tuple[float, T]] = {}

    @property
    def ttl(self) -> float:
        return self._ttl

    def get(self, key: str) -> T | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts >= self._ttl:
            return None
        return value

    def set(self, key: str, value: T) -> None:
        self._data[key] = (time.monotonic(), value)

    def invalidate(self, key: str) -> None:
        self._data.pop(key, None)

    def sweep_stale(self, factor: float = 10.0) -> int:
        """Удалить записи, которые протухли более чем в factor раз TTL."""
        now = time.monotonic()
        threshold = self._ttl * factor
        stale = [k for k, (ts, _) in list(self._data.items()) if now - ts > threshold]
        for k in stale:
            self._data.pop(k, None)
        return len(stale)

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __setitem__(self, key: str, value: tuple[float, T]) -> None:
        # Совместимость с прежним dict-интерфейсом: значение приходит как (ts, payload).
        self._data[key] = value

    def __getitem__(self, key: str) -> tuple[float, T]:
        return self._data[key]

    def items(self):
        return self._data.items()

    def pop(self, key: str, default=None):
        return self._data.pop(key, default)
