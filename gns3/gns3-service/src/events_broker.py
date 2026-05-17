"""Redis Streams-backed event broker.

Replaces previous in-process dict broker. Enables multi-replica gns3-service.

Stream key: sessions:{session_id}:events
Producer: XADD with MAXLEN ~ 1000 (trim approximation)
Consumer: XREAD BLOCK with $ for tail-following
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class EventBroker:
    def __init__(self, redis_url: str) -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)

    def _stream_key(self, session_id: str) -> str:
        return f"sessions:{session_id}:events"

    async def publish(self, session_id: str, event: dict) -> None:
        try:
            payload = json.dumps(event)
        except (TypeError, ValueError):
            logger.exception("Failed to serialize event for session=%s", session_id)
            return
        try:
            await self._redis.xadd(
                self._stream_key(session_id),
                {"payload": payload},
                maxlen=1000,
                approximate=True,
            )
        except Exception:
            logger.exception("XADD failed for session=%s", session_id)

    async def subscribe(self, session_id: str) -> AsyncIterator[dict]:
        """Async-итератор. Стартует с $, только tail-following без replay."""
        last_id = "$"
        stream_key = self._stream_key(session_id)
        while True:
            try:
                result = await self._redis.xread(
                    {stream_key: last_id},
                    block=5000,
                    count=100,
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("xread failed for %s", stream_key)
                await asyncio.sleep(1)
                continue
            if not result:
                continue
            for _, entries in result:
                for entry_id, fields in entries:
                    last_id = entry_id
                    try:
                        yield json.loads(fields["payload"])
                    except Exception:
                        logger.exception("Bad event payload in %s: %r", stream_key, fields)

    async def close(self) -> None:
        await self._redis.aclose()
