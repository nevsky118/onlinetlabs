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
# Средняя длительность провижининга одной сессии, используется для ETA в очереди.
QUEUE_AVG_PROVISION_SEC = 30

# Атомарный захват слота. Под нагрузкой 50+/sec обычная пара GET/INCR
# протекает квоту, потому что между чтением и инкрементом успевает зайти
# параллельный запрос. Lua выполняется в Redis монолитно — счётчики
# либо инкрементятся вместе, либо запрос отказывает.
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


class SessionQueueService:
    """Очередь сессий и счётчики активных сессий поверх Redis.

    Атомарно захватывает и освобождает слоты под лимиты по лаборатории и общий,
    ведёт FIFO-очередь ожидающих по каждой лаборатории.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        """Создаёт клиент Redis из переданного URL или настроек."""
        self._redis = aioredis.from_url(redis_url or settings.redis.url, decode_responses=True)

    def _active_key(self, lab_slug: str) -> str:
        """Ключ Redis со счётчиком активных сессий лаборатории."""
        return f"active_sessions:{lab_slug}"

    def _queue_key(self, lab_slug: str) -> str:
        """Ключ Redis с очередью ожидающих по лаборатории."""
        return f"queue:{lab_slug}"

    def _total_key(self) -> str:
        """Ключ Redis с общим счётчиком активных сессий."""
        return "active_sessions_total"

    async def try_acquire(self, user_id: str, lab_slug: str) -> bool:
        """Пытается атомарно занять слот сессии. True если слот захвачен, иначе False."""
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
        """Освобождает слот, уменьшая счётчики лаборатории и общий."""
        async with self._redis.pipeline(transaction=True) as pipe:
            await pipe.decr(self._active_key(lab_slug))
            await pipe.decr(self._total_key())
            await pipe.execute()

    async def enqueue(self, user_id: str, lab_slug: str) -> int:
        """Добавляет пользователя в конец очереди и возвращает её длину."""
        await self._redis.rpush(
            self._queue_key(lab_slug),
            json.dumps({"user_id": user_id, "ts": int(time.time())}),
        )
        return await self._redis.llen(self._queue_key(lab_slug))

    async def position(self, user_id: str, lab_slug: str) -> int | None:
        """Возвращает позицию пользователя в очереди начиная с 1 или None если его нет."""
        items = await self._redis.lrange(self._queue_key(lab_slug), 0, -1)
        for i, raw in enumerate(items):
            if json.loads(raw)["user_id"] == user_id:
                return i + 1
        return None

    async def queue_depth(self, lab_slug: str) -> int:
        """Возвращает текущее число ожидающих в очереди лаборатории."""
        return await self._redis.llen(self._queue_key(lab_slug))


# Модульный синглтон и DI-провайдер.
#
# Сервис создаётся в lifespan и кладётся в app.state.session_queue.
# get_queue_service() читает его через FastAPI Request. Если состояния нет
# (тесты, фоновые задачи без app), фоллбекаем на lazy-инициализированный
# модульный синглтон, чтобы старые callers не падали.
_queue_singleton: SessionQueueService | None = None


def _get_or_create_singleton() -> SessionQueueService:
    """Лениво создаёт и возвращает модульный синглтон сервиса очереди."""
    global _queue_singleton
    if _queue_singleton is None:
        _queue_singleton = SessionQueueService()
    return _queue_singleton


def get_queue_service(request: Request) -> SessionQueueService:
    """FastAPI-зависимость: возвращает session_queue из app.state.

    В lifespan кладём SessionQueueService в app.state. Если по какой-то
    причине его там нет (старый код, миграция), фоллбекаем на ленивый
    модульный синглтон, чтобы не уронить запрос.
    """
    existing = getattr(request.app.state, "session_queue", None)
    if existing is not None:
        return existing
    return _get_or_create_singleton()
