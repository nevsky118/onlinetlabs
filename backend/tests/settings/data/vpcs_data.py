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
