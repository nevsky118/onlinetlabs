# Сериализация записей в RBAC GNS3 (пользователи и ACL).

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_LOCK_KEY = "lock:gns3_rbac_write"


class RbacGate:
    """Пропускает записи в RBAC GNS3 строго по одной.

    GNS3-сервер отдаёт 500 на параллельных `POST /v3/access/acl` — его RBAC-хранилище
    не выдерживает конкурентных записей. Ретраи не помогают: конкурирующие провижны
    сталкиваются снова (на 5 одновременных студентах ~60% сессий не создавалось).
    Поэтому создание пользователя и ACL прогоняются через гейт.

    Локальный `asyncio.Lock` сериализует внутри процесса; Redis-лок (если задан URL)
    добавляет сериализацию между репликами gns3-service. Тяжёлое `duplicate_project`
    через гейт НЕ идёт — оно не трогает RBAC и должно оставаться параллельным.
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
        """Redis-лок с TTL (переживает падение реплики). None, если Redis не настроен."""
        if self._redis is None:
            return None
        token = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._wait_timeout
        while True:
            try:
                acquired = await self._redis.set(
                    _LOCK_KEY, token, nx=True, ex=self._lock_ttl
                )
            except Exception:
                # Redis недоступен → не блокируем провижн: локального лока достаточно
                # для одиночной реплики (текущий деплой).
                logger.warning("RBAC-гейт: Redis недоступен, работаем на локальном локе",
                               exc_info=True)
                return None
            if acquired:
                return token
            if loop.time() >= deadline:
                logger.warning("RBAC-гейт: ждали лок %.0fs, продолжаем без него",
                               self._wait_timeout)
                return None
            await asyncio.sleep(self._poll_interval)

    async def _release_distributed(self, token: str | None) -> None:
        """Снимаем лок только если он всё ещё наш (TTL мог истечь и его перехватили)."""
        if self._redis is None or token is None:
            return
        try:
            current = await self._redis.get(_LOCK_KEY)
            if current == token:
                await self._redis.delete(_LOCK_KEY)
        except Exception:
            logger.warning("RBAC-гейт: не удалось снять Redis-лок", exc_info=True)
