"""Unit tests for RbacGate, serialization of writes into the GNS3 RBAC.

Regression. The GNS3 server returns a 500 on concurrent POST /v3/access/acl.
Retries did not help, competing provisioning runs collided again (with 5
simultaneous students roughly 60% of sessions were not created). The gate lets
RBAC writes through strictly one at a time.
"""

import asyncio

import pytest

from src.rbac_gate import RbacGate


class TestRbacGate:
    """The gate serializes the RBAC critical section."""

    @pytest.mark.asyncio
    async def test_serializes_concurrent_sections(self):
        """Concurrent calls do not overlap inside the gate."""
        gate = RbacGate()  # no Redis, local lock only
        overlaps = 0
        inside = 0

        async def rbac_write():
            nonlocal overlaps, inside
            async with gate():
                inside += 1
                if inside > 1:
                    overlaps += 1
                await asyncio.sleep(0.01)  # hold the section
                inside -= 1

        await asyncio.gather(*(rbac_write() for _ in range(8)))

        assert overlaps == 0, "внутри гейта одновременно был больше чем один писатель"
        assert inside == 0

    @pytest.mark.asyncio
    async def test_releases_lock_on_exception(self):
        """An exception inside the section does not leave the gate locked."""
        gate = RbacGate()

        with pytest.raises(RuntimeError):
            async with gate():
                raise RuntimeError("GNS3 500")

        # The gate is passable again, otherwise provisioning would stall forever.
        async with gate():
            pass

    @pytest.mark.asyncio
    async def test_works_without_redis(self):
        """Without Redis the gate runs on the local lock (single replica)."""
        gate = RbacGate(redis_url=None)
        entered = False

        async with gate():
            entered = True

        assert entered is True

    @pytest.mark.asyncio
    async def test_redis_failure_does_not_block_provisioning(self, monkeypatch):
        """An unavailable Redis must not break provisioning, the local lock remains."""
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
