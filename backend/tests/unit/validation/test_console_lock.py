"""One reader at a time per node console: the observer must not race a student's check."""

import asyncio
from unittest.mock import patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from validation.checks.vpcs import console

pytestmark = [pytest.mark.unit]

_HOST = "gns3-server"
_PORT = 2011


class _Writer:
    """A writer that records nothing and closes cleanly."""

    def close(self) -> None:
        """No-op close."""

    async def wait_closed(self) -> None:
        """No-op wait."""


class TestConsoleLock:
    @autotest.num("3445")
    @autotest.external_id("8ce079b2-30cf-4d4c-b69d-5a6dd4d44918")
    @autotest.name("console: two readers of one node never overlap")
    async def test_8ce079b2_same_node_is_serialised(self):
        with autotest.step("Arrange: a connect that records concurrency"):
            live = 0
            peak = 0

            async def _open(host, port):
                return object(), _Writer()

            async def use():
                nonlocal live, peak
                async with console(_HOST, _PORT):
                    live += 1
                    peak = max(peak, live)
                    await asyncio.sleep(0.02)
                    live -= 1

        with autotest.step("Act: four readers hit the same console at once"):
            with patch("validation.checks.vpcs._open_console", _open):
                await asyncio.gather(*(use() for _ in range(4)))

        with autotest.step("Assert: never more than one at a time"):
            assert_equal(peak, 1, "serialised")

    @autotest.num("3446")
    @autotest.external_id("a7429a8b-ae79-40b2-9081-ea2f8dc316fd")
    @autotest.name("console: different nodes are not serialised against each other")
    async def test_a7429a8b_distinct_nodes_run_in_parallel(self):
        with autotest.step("Arrange: two different console ports"):
            live = 0
            peak = 0

            async def _open(host, port):
                return object(), _Writer()

            async def use(port):
                nonlocal live, peak
                async with console(_HOST, port):
                    live += 1
                    peak = max(peak, live)
                    await asyncio.sleep(0.02)
                    live -= 1

        with autotest.step("Act: read two nodes at once"):
            with patch("validation.checks.vpcs._open_console", _open):
                await asyncio.gather(use(2011), use(2013))

        with autotest.step("Assert: the lock is per node, not global"):
            assert_true(peak == 2, "distinct nodes overlap")
