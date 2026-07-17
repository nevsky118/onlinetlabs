"""Unit-тесты RbacGate: сериализация записей в RBAC GNS3.

Регрессия: GNS3-сервер отдаёт 500 на параллельных POST /v3/access/acl. Ретраи не
спасали — конкурирующие провижны сталкивались снова (на 5 одновременных студентах
~60% сессий не создавалось). Гейт пропускает RBAC-записи строго по одной.
"""

import asyncio

import pytest

from src.rbac_gate import RbacGate


class TestRbacGate:
    """Гейт сериализует критическую секцию RBAC."""

    @pytest.mark.asyncio
    async def test_serializes_concurrent_sections(self):
        """Параллельные вызовы не пересекаются внутри гейта."""
        gate = RbacGate()  # без Redis: только локальный лок
        overlaps = 0
        inside = 0

        async def rbac_write():
            nonlocal overlaps, inside
            async with gate():
                inside += 1
                if inside > 1:
                    overlaps += 1
                await asyncio.sleep(0.01)  # удерживаем секцию
                inside -= 1

        await asyncio.gather(*(rbac_write() for _ in range(8)))

        assert overlaps == 0, "внутри гейта одновременно был больше чем один писатель"
        assert inside == 0

    @pytest.mark.asyncio
    async def test_releases_lock_on_exception(self):
        """Исключение внутри секции не оставляет гейт заблокированным."""
        gate = RbacGate()

        with pytest.raises(RuntimeError):
            async with gate():
                raise RuntimeError("GNS3 500")

        # Гейт снова проходим — иначе провижн встал бы навсегда.
        async with gate():
            pass

    @pytest.mark.asyncio
    async def test_works_without_redis(self):
        """Без Redis гейт работает на локальном локе (одиночная реплика)."""
        gate = RbacGate(redis_url=None)
        entered = False

        async with gate():
            entered = True

        assert entered is True

    @pytest.mark.asyncio
    async def test_redis_failure_does_not_block_provisioning(self, monkeypatch):
        """Недоступный Redis не должен ронять провижн: остаётся локальный лок."""
        gate = RbacGate()

        class _BrokenRedis:
            async def set(self, *_args, **_kwargs):
                raise ConnectionError("redis down")

            async def get(self, *_args, **_kwargs):
                raise ConnectionError("redis down")

            async def delete(self, *_args, **_kwargs):
                raise ConnectionError("redis down")

        monkeypatch.setattr(gate, "_redis", _BrokenRedis())

        entered = False
        async with gate():
            entered = True

        assert entered is True, "падение Redis не должно блокировать RBAC-запись"
