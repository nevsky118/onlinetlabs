"""Unit tests for the vpcs.ping check handler."""

import asyncio
from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_false, assert_true

from tests.settings.data.vpcs_data import VpcsPingConsoleData
from validation.checks import vpcs

pytestmark = [pytest.mark.unit]


class _Writer:
    """Console writer that records what the handler sent."""

    def __init__(self, sink: list[bytes]):
        self._sink = sink

    def write(self, data: bytes) -> None:
        self._sink.append(data)

    async def drain(self) -> None:
        return None

    def close(self) -> None:
        return None

    async def wait_closed(self) -> None:
        return None


def _patch_console(monkeypatch, console: VpcsPingConsoleData) -> list[bytes]:
    """Patch the console transport, return the list collecting written bytes."""
    writes: list[bytes] = []
    pending = list(console.replies)

    async def fake_open_connection(host, port):
        return object(), _Writer(writes)

    async def fake_drain(reader, timeout):
        return pending.pop(0) if pending else b""

    monkeypatch.setattr(asyncio, "open_connection", fake_open_connection)
    monkeypatch.setattr(vpcs, "_drain_until_prompt", fake_drain)
    return writes


def _ctx() -> SimpleNamespace:
    """Minimal check context exposing the console endpoint of a node."""
    return SimpleNamespace(
        node_console_port=lambda name: 2002,
        node_console_host=lambda name: "gns3-server",
    )


class TestVpcsPingArpWarmup:
    """The first VPCS ping resolves ARP and loses probes, so it must not be measured."""

    @autotest.num("3384")
    @autotest.external_id("3632a1f6-cfca-47b0-a02c-987a16d9e1ad")
    @autotest.name("vpcs.ping: discards the cold ARP ping and reports the warm one")
    async def test_3632a1f6_discards_cold_arp_attempt(self, monkeypatch):
        with autotest.step("Arrange: a console whose first ping loses probes to ARP"):
            console = VpcsPingConsoleData.cold_then_warm()
            writes = _patch_console(monkeypatch, console)

        with autotest.step("Act: run the vpcs.ping check"):
            result = await vpcs.vpcs_ping(
                _ctx(), {"from": "PC1", "to": console.first.target}, {"received": ">=4"}
            )

        with autotest.step("Assert: two pings were sent and the warm result is reported"):
            assert_equal(sum(1 for w in writes if w.startswith(b"ping ")), 2, "two pings sent")
            assert_equal(
                result.actual["received"], console.second.replies, "received from second ping"
            )
            assert_true(result.ok, "a configured lab passes on the first validation run")

    @autotest.num("3390")
    @autotest.external_id("a4f0c1d8-9e2b-4c33-8f5a-1d7b6e0a2c94")
    @autotest.name("vpcs.ping: a genuinely unreachable target still fails")
    async def test_a4f0c1d8_unreachable_target_still_fails(self, monkeypatch):
        with autotest.step("Arrange: a console where neither ping gets a reply"):
            console = VpcsPingConsoleData.unreachable()
            _patch_console(monkeypatch, console)

        with autotest.step("Act: run the vpcs.ping check"):
            result = await vpcs.vpcs_ping(
                _ctx(), {"from": "PC1", "to": console.first.target}, {"received": ">=4"}
            )

        with autotest.step("Assert: the warm-up does not mask a real failure"):
            assert_equal(result.actual["received"], 0, "no replies received")
            assert_false(result.ok, "the check fails")
