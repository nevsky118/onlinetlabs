# Test data generators for VPCS console output.

import asyncio

_DEFAULT_TARGET = "192.168.1.12"
_PROMPT = "VPCS> "
_PROMPT_BYTES = b"VPCS> "


class VpcsPingOutputData:
    """Generates the console text VPCS prints for one `ping` command.

    `replies` is how many of the five probes answered: 5 is a warm cache, 1 is the
    cold-ARP first attempt, 0 is a genuinely unreachable target.
    """

    def __init__(self, replies: int = 5, target: str = _DEFAULT_TARGET, ttl: int = 64):
        self.target = target
        self.replies = replies
        self.ttl = ttl
        lines = [f"ping {target}"]
        if replies < 5:
            lines.append(f"host ({target}) not reachable")
        for seq in range(5 - replies + 1, 6):
            lines.append(f"84 bytes from {target} icmp_seq={seq} ttl={ttl} time=0.6 ms")
        self.text = "\r\n".join(lines) + "\r\n" + _PROMPT

    @property
    def encoded(self) -> bytes:
        """Console text as the bytes the reader yields."""
        return self.text.encode()


class VpcsPingConsoleData:
    """Generates the ordered console replies a vpcs.ping run reads.

    The banner is drained separately, so the sequence is first ping, then second ping.
    """

    def __init__(self, first: VpcsPingOutputData, second: VpcsPingOutputData):
        self.first = first
        self.second = second
        self.replies = [first.encoded, second.encoded]

    @classmethod
    def cold_then_warm(cls, target: str = _DEFAULT_TARGET) -> "VpcsPingConsoleData":
        """ARP resolves on the first ping, the second one answers fully."""
        return cls(
            VpcsPingOutputData(replies=1, target=target),
            VpcsPingOutputData(replies=5, target=target),
        )

    @classmethod
    def unreachable(cls, target: str = _DEFAULT_TARGET) -> "VpcsPingConsoleData":
        """Neither ping gets a reply."""
        return cls(
            VpcsPingOutputData(replies=0, target=target),
            VpcsPingOutputData(replies=0, target=target),
        )


class VpcsShowIpConsoleData:
    """Generates a console whose banner arrives in chunks, then answers `show ip`.

    A banner split across reads is what makes a prompt-terminated preamble drain stop
    early and leave a stale prompt behind.
    """

    def __init__(self, ip: str = "192.168.1.11/24", gateway: str = "192.168.1.1"):
        self.ip = ip
        self.gateway = gateway
        self.banner_chunks = [b"\r\n", _PROMPT_BYTES, b"\r\n" + _PROMPT_BYTES]
        self.show_ip = (
            "show ip\r\n"
            "NAME        : VPCS[1]\r\n"
            f"IP/MASK     : {ip}\r\n"
            f"GATEWAY     : {gateway}\r\n"
            "MTU         : 1500\r\n"
            "VPCS> "
        ).encode()


class VpcsStalePromptConsoleData:
    """Generates a console that answers the first `show ip` with only a stale prompt.

    That is what a reconnect right after the previous check closed the same console
    looks like: a reply that parses as no address rather than a wrong one.
    """

    def __init__(self, ip: str = "192.168.1.11/24", gateway: str = "192.168.1.1"):
        self.ip = ip
        self.gateway = gateway
        self.stale = _PROMPT_BYTES
        self.answer = (
            f"show ip\r\nIP/MASK     : {ip}\r\nGATEWAY     : {gateway}\r\nVPCS> "
        ).encode()


class VpcsSaveConsoleData:
    """Generates the console reply to `save`, as captured from a real VPCS node."""

    def __init__(self, node: str = "PC1", started: bool = True):
        self.node = node
        self.started = started
        self.ok_text = (
            "save\r\nSaving startup configuration to startup.vpc\r\n.  done\r\n\r\n\rVPCS> "
        )
        self.silent_text = "\r\nVPCS> "
        self.truncated_text = "save\r\nSaving startup configuration to startup.vpc\r\n"

    @property
    def ok(self) -> bytes:
        """A completed save."""
        return self.ok_text.encode()

    @property
    def silent(self) -> bytes:
        """A console that answered with nothing but a prompt."""
        return self.silent_text.encode()

    @property
    def truncated(self) -> bytes:
        """A save that started and never reported done."""
        return self.truncated_text.encode()


class Gns3NodeStateData:
    """Generates the node dicts a CheckContext holds.

    Two shapes exist: gns3-service sends snake_case over the wire, while the
    backend's own session-state response renames the same fields to camelCase.
    """

    def __init__(self, camel: bool = False):
        self.camel = camel
        self.nodes = {
            "SW1": self._node("ethernet_switch", 2010, "none", "started"),
            "PC1": self._node("vpcs", 2011, "telnet", "started"),
            "PC2": self._node("vpcs", 2013, "telnet", "started"),
        }

    def _node(self, node_type: str, console: int, console_type: str, status: str) -> dict:
        """One node entry in the configured shape."""
        keys = (
            ("nodeType", "consoleHost", "consoleType")
            if self.camel
            else ("node_type", "console_host", "console_type")
        )
        return {
            "id": f"node-{console}",
            "name": f"n{console}",
            keys[0]: node_type,
            "console": console,
            keys[1]: "0.0.0.0",
            keys[2]: console_type,
            "status": status,
        }

    def with_stopped(self, name: str) -> "Gns3NodeStateData":
        """Marks one node stopped, so it must be skipped."""
        self.nodes[name] = {**self.nodes[name], "status": "stopped"}
        return self

    @property
    def vpcs_ports(self) -> list[int]:
        """Console ports of started vpcs nodes, which are the save targets."""
        from validation.checks.registry import CheckContext

        ctx = CheckContext(gns3_host="gns3", nodes_by_name=self.nodes)
        return [
            value["console"]
            for name, value in self.nodes.items()
            if ctx.node_type(name) == "vpcs" and ctx.node_status(name) == "started"
        ]


class ConsoleWriterData:
    """Console writer that records what the handler sent, and closes cleanly."""

    def __init__(self, sink: list | None = None):
        self.sink = sink if sink is not None else []

    def write(self, data: bytes) -> None:
        """Records the bytes instead of sending them."""
        self.sink.append(data)

    async def drain(self) -> None:
        """No-op drain."""

    def close(self) -> None:
        """No-op close."""

    async def wait_closed(self) -> None:
        """No-op wait."""


class ConsoleReaderData:
    """Console reader that yields queued chunks, then goes quiet until more are queued."""

    def __init__(self, chunks: list):
        self.chunks = list(chunks)

    def queue(self, chunk: bytes) -> None:
        """Makes another chunk available to the next read."""
        self.chunks.append(chunk)

    async def read(self, _n: int) -> bytes:
        """The next queued chunk, or a wait that never returns."""
        if self.chunks:
            return self.chunks.pop(0)
        await asyncio.sleep(3600)


class AnsweringConsoleWriterData(ConsoleWriterData):
    """Writer that makes the console answer only after the command is sent."""

    def __init__(self, sink: list, reader: ConsoleReaderData, command: bytes, answer: bytes):
        super().__init__(sink)
        self.reader = reader
        self.command = command
        self.answer = answer

    def write(self, data: bytes) -> None:
        """Records the bytes and queues the reply when the command goes out."""
        super().write(data)
        if data.startswith(self.command):
            self.reader.queue(self.answer)
