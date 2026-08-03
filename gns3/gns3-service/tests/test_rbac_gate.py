"""Unit tests for RbacGate, serialization of writes into the GNS3 RBAC.

Regression. The GNS3 server returns a 500 on concurrent POST /v3/access/acl.
Retries did not help, competing provisioning runs collided again (with 5
simultaneous students roughly 60% of sessions were not created). The gate lets
RBAC writes through strictly one at a time.
"""

import asyncio

import pytest
from mcp_sdk.testing import autotest

from src.rbac_gate import RbacGate


class TestRbacGate:
    """The gate serializes the RBAC critical section."""

    @pytest.mark.asyncio
    @autotest.num("3345")
    @autotest.external_id("871f5ee7-04cb-4aaa-b04f-2bdfb9227093")
    @autotest.name("RbacGate: concurrent calls do not overlap inside the gate")
    async def test_871f5ee7_serializes_concurrent_sections(self):
        """Concurrent calls do not overlap inside the gate."""
        with autotest.step("Arrange: a gate and a section that counts overlaps"):
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

        with autotest.step("Act: run 8 writers through the gate concurrently"):
            await asyncio.gather(*(rbac_write() for _ in range(8)))

        with autotest.step("Assert: no two writers were inside the gate at once"):
            assert overlaps == 0, "more than one writer was inside the gate at once"
            assert inside == 0

    @pytest.mark.asyncio
    @autotest.num("3346")
    @autotest.external_id("74a2f4ed-f6d2-44a5-a49d-3406a04c6a95")
    @autotest.name("RbacGate: an exception inside the section releases the lock")
    async def test_74a2f4ed_releases_lock_on_exception(self):
        """An exception inside the section does not leave the gate locked."""
        with autotest.step("Arrange: a gate"):
            gate = RbacGate()

        with autotest.step("Act + Assert: an exception inside the section propagates"):
            with pytest.raises(RuntimeError):
                async with gate():
                    raise RuntimeError("GNS3 500")

        with autotest.step("Assert: the gate is passable again afterwards"):
            # The gate is passable again, otherwise provisioning would stall forever.
            async with gate():
                pass

    @pytest.mark.asyncio
    @autotest.num("3347")
    @autotest.external_id("4834c103-b31e-4fb9-82c4-37fdf6d081fe")
    @autotest.name("RbacGate: runs on the local lock without Redis")
    async def test_4834c103_works_without_redis(self):
        """Without Redis the gate runs on the local lock (single replica)."""
        with autotest.step("Arrange: a gate with no Redis URL"):
            gate = RbacGate(redis_url=None)
            entered = False

        with autotest.step("Act: enter the gate's section"):
            async with gate():
                entered = True

        with autotest.step("Assert: the section was entered"):
            assert entered is True

    @pytest.mark.asyncio
    @autotest.num("3348")
    @autotest.external_id("3a09896d-ce27-411f-8ecd-1944f93dea45")
    @autotest.name("RBAC gate: a Redis outage does not block the write")
    async def test_3a09896d_redis_failure_does_not_block_provisioning(self, monkeypatch):
        """An unavailable Redis must not break provisioning, the local lock remains."""
        with autotest.step("Arrange: a gate whose Redis client always raises"):
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

        with autotest.step("Act: enter the gate's section despite the Redis outage"):
            async with gate():
                entered = True

        with autotest.step("Assert: the section was entered regardless of Redis"):
            assert entered is True, "a Redis outage must not block the RBAC write"
