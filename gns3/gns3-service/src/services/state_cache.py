# In-memory cache of session state snapshots with TTL.
#
# Purpose: collapse burst requests from UI/WS without hitting GNS3 on every render.

from __future__ import annotations

import time
from typing import Generic, TypeVar

T = TypeVar("T")


class StateCache(Generic[T]):
    """Simple TTL cache keyed by session.

    Not thread-safe in the strict sense, but that's enough within a single event loop.
    """

    def __init__(self, ttl_seconds: float = 5.0) -> None:
        self._ttl = ttl_seconds
        self._data: dict[str, tuple[float, T]] = {}

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
        """Remove entries that are stale by more than factor times the TTL."""
        now = time.monotonic()
        threshold = self._ttl * factor
        stale = [k for k, (ts, _) in list(self._data.items()) if now - ts > threshold]
        for k in stale:
            self._data.pop(k, None)
        return len(stale)
