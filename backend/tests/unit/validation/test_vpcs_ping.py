"""Unit tests for the vpcs.ping check handler."""

import asyncio
from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_false, assert_true

from tests.settings.data.vpcs_data import (
    VpcsPingConsoleData,
    VpcsShowIpConsoleData,
    VpcsStalePromptConsoleData,
)
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


class _Reader:
    """Console reader that yields queued chunks, then goes quiet until more are queued."""

    def __init__(self, chunks: list[bytes]):
        self._chunks = list(chunks)

    def queue(self, chunk: bytes) -> None:
        self._chunks.append(chunk)

    async def read(self, _n: int) -> bytes:
        if self._chunks:
            return self._chunks.pop(0)
        await asyncio.sleep(3600)


class _AnsweringWriter(_Writer):
    """Writer that makes the console answer only after the command is sent."""

    def __init__(self, sink: list[bytes], reader: _Reader, command: bytes, answer: bytes):
        super().__init__(sink)
        self._reader = reader
        self._command = command
        self._answer = answer

    def write(self, data: bytes) -> None:
        super().write(data)
        if data.startswith(self._command):
            self._reader.queue(self._answer)


def _patch_console(monkeypatch, console: VpcsPingConsoleData) -> list[bytes]:
    """Patch the console transport, return the list collecting written bytes."""
    writes: list[bytes] = []
    pending = list(console.replies)

    async def fake_open_connection(host, port):
        return object(), _Writer(writes)

    async def fake_drain(reader, timeout):
        return pending.pop(0) if pending else b""

    async def no_preamble(reader, idle, total):
        return b""

    monkeypatch.setattr(asyncio, "open_connection", fake_open_connection)
    monkeypatch.setattr(vpcs, "_drain_idle", no_preamble)
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


class TestVpcsShowIpChunkedBanner:
    """A banner split across reads must not be mistaken for the command's answer."""

    @autotest.num("3391")
    @autotest.external_id("65773a61-953a-4ea1-b7db-7b7280e8d368")
    @autotest.name("vpcs.show_ip: a chunked banner does not truncate the reply")
    async def test_65773a61_chunked_banner_does_not_truncate_reply(self, monkeypatch):
        with autotest.step("Arrange: a console whose banner arrives as three chunks"):
            console = VpcsShowIpConsoleData()

            reader = _Reader(console.banner_chunks)
            writer = _AnsweringWriter([], reader, b"show ip", console.show_ip)

            async def fake_open_connection(host, port):
                return reader, writer

            monkeypatch.setattr(asyncio, "open_connection", fake_open_connection)

        with autotest.step("Act: run the vpcs.show_ip check"):
            result = await vpcs.vpcs_show_ip(
                _ctx(), {"node": "PC1"}, {"ip": console.ip, "gateway": console.gateway}
            )

        with autotest.step("Assert: the reply is parsed, not reported as empty"):
            assert_equal(result.actual["ip"], console.ip, "ip parsed")
            assert_equal(result.actual["gateway"], console.gateway, "gateway parsed")
            assert_true(result.ok, "a configured PC passes")


class TestVpcsShowIpStalePrompt:
    """A stale prompt means the answer never arrived, so it is asked again."""

    @autotest.num("3392")
    @autotest.external_id("4df7c1bb-daba-4c2b-860d-b9d04c894a74")
    @autotest.name("vpcs.show_ip: retries once when the first reply is only a stale prompt")
    async def test_4df7c1bb_retries_once_on_stale_prompt(self, monkeypatch):
        with autotest.step("Arrange: the first show ip returns a bare prompt"):
            console = VpcsStalePromptConsoleData()
            reader = _Reader([])
            sent: list[bytes] = []
            replies = [console.stale, console.answer]

            class _Retrying(_Writer):
                def write(self, data: bytes) -> None:
                    super().write(data)
                    if data.startswith(b"show ip") and replies:
                        reader.queue(replies.pop(0))

            writer = _Retrying(sent)

            async def fake_open_connection(host, port):
                return reader, writer

            monkeypatch.setattr(asyncio, "open_connection", fake_open_connection)

        with autotest.step("Act: run the vpcs.show_ip check"):
            result = await vpcs.vpcs_show_ip(
                _ctx(), {"node": "PC1"}, {"ip": console.ip, "gateway": console.gateway}
            )

        with autotest.step("Assert: asked twice and parsed the second reply"):
            assert_equal(sum(1 for w in sent if w.startswith(b"show ip")), 2, "asked twice")
            assert_equal(result.actual["ip"], console.ip, "ip parsed")
            assert_true(result.ok, "a configured PC passes")
