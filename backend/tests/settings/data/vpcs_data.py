# Test data generators for VPCS console output.

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
    """Generates the node dicts a CheckContext holds, in the camelCase gns3 shape."""

    def __init__(self):
        self.nodes = {
            "SW1": self._node("ethernet_switch", 2010, "none", "started"),
            "PC1": self._node("vpcs", 2011, "telnet", "started"),
            "PC2": self._node("vpcs", 2013, "telnet", "started"),
        }

    @staticmethod
    def _node(node_type: str, console: int, console_type: str, status: str) -> dict:
        """One node entry as gns3-service serializes it."""
        return {
            "id": f"node-{console}",
            "name": f"n{console}",
            "nodeType": node_type,
            "console": console,
            "consoleHost": "0.0.0.0",
            "consoleType": console_type,
            "status": status,
        }

    def with_stopped(self, name: str) -> "Gns3NodeStateData":
        """Marks one node stopped, so it must be skipped."""
        self.nodes[name] = {**self.nodes[name], "status": "stopped"}
        return self

    @property
    def vpcs_ports(self) -> list[int]:
        """Console ports of started vpcs nodes, which are the save targets."""
        return [
            n["console"]
            for n in self.nodes.values()
            if n["nodeType"] == "vpcs" and n["status"] == "started"
        ]
