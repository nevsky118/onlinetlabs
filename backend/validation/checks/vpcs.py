"""VPCS check handlers: `vpcs.show_ip`, `vpcs.ping`."""

import asyncio
import ipaddress
import re
from contextlib import asynccontextmanager

from validation.checks.registry import CheckContext, CheckResult

_IP_RE = re.compile(r"IP/MASK\s*:\s*(\S+)", re.IGNORECASE)
_GW_RE = re.compile(r"GATEWAY\s*:\s*(\S+)", re.IGNORECASE)

# Each successful VPCS-ping reply line looks like:
#   `84 bytes from 192.168.20.10 icmp_seq=1 ttl=62 time=2.345 ms`
_PING_REPLY_RE = re.compile(r"^\s*\d+\s+bytes\s+from\s+\S+", re.MULTILINE)
_PING_TTL_RE = re.compile(r"\bttl=(\d+)", re.IGNORECASE)
# VPCS prints one of these when the target is genuinely unreachable; without any of
# them and without replies the console simply did not answer.
_PING_UNREACHABLE_RE = re.compile(r"not reachable|timeout|host unreachable", re.IGNORECASE)
# VPCS prints "Saving startup configuration to startup.vpc" then ".  done".
_SAVE_OK_RE = re.compile(r"saving startup configuration.*?done", re.IGNORECASE | re.DOTALL)
# `>=N` / `>N` / `==N` / `=N` / `N`. Strict equality by default.
_COMPARE_RE = re.compile(r"^\s*(>=|<=|==|=|>|<)?\s*(\d+)\s*$")

_CONNECT_TIMEOUT = 5.0
_CONNECT_ATTEMPTS = 4
_READ_ATTEMPTS = 3
_READ_BACKOFF = 0.5
_CONNECT_BACKOFF = 0.4
_READ_TIMEOUT = 3.0
_PING_READ_TIMEOUT = 8.0
_SAVE_TIMEOUT = 15.0
_PROMPT = b"> "


async def _open_console(host: str, port: int):
    """Open the node console, retrying while a previous session is still closing.

    GNS3 serialises telnet consoles per node, so a reconnect right after the previous
    check closed one is refused rather than queued.
    """
    last: Exception | None = None
    for attempt in range(_CONNECT_ATTEMPTS):
        if attempt:
            await asyncio.sleep(_CONNECT_BACKOFF * attempt)
        try:
            async with asyncio.timeout(_CONNECT_TIMEOUT):
                return await asyncio.open_connection(host, port)
        except (TimeoutError, OSError) as exc:
            last = exc
    raise last if last else OSError("console connect failed")


# GNS3 serialises telnet consoles per node: a second client is refused, not queued.
# The progress observer and a student's validation run otherwise fight over the
# same console and one of them reads nothing.
_console_locks: dict[tuple[str, int], asyncio.Lock] = {}


def _console_lock(host: str, port: int) -> asyncio.Lock:
    """The lock guarding one node's console."""
    key = (host, port)
    lock = _console_locks.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _console_locks[key] = lock
    return lock


@asynccontextmanager
async def console(host: str, port: int):
    """Exclusive console session. Connects, yields (reader, writer), always closes."""
    async with _console_lock(host, port):
        reader, writer = await _open_console(host, port)
        try:
            yield reader, writer
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass


async def _drain_idle(reader: asyncio.StreamReader, idle: float, total: float) -> bytes:
    """Read until the console stays quiet for `idle` seconds, or `total` elapses.

    Stopping at the first prompt leaves later banner chunks buffered, and the next
    read then returns that stale prompt before the command has answered.
    """
    buf = bytearray()
    loop = asyncio.get_running_loop()
    deadline = loop.time() + total
    while True:
        remaining = min(idle, deadline - loop.time())
        if remaining <= 0:
            break
        try:
            chunk = await asyncio.wait_for(reader.read(1024), timeout=remaining)
        except TimeoutError:
            break
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf)


async def _drain_until_prompt(reader: asyncio.StreamReader, timeout: float) -> bytes:
    """Read from the console until a VPCS prompt appears or the timeout elapses."""
    buf = bytearray()
    try:
        async with asyncio.timeout(timeout):
            while True:
                chunk = await reader.read(1024)
                if not chunk:
                    break
                buf.extend(chunk)
                if _PROMPT in buf:
                    break
    except TimeoutError:
        pass
    return bytes(buf)


async def _read_show_ip(reader, writer) -> bytes:
    """Ask the console for `show ip`, retrying once when the reply comes back empty.

    A reconnect right after the previous check closed the same console can yield a
    stale prompt, which parses as no address rather than a wrong one.
    """
    for attempt in range(2):
        if attempt:
            await _drain_idle(reader, idle=0.3, total=1.0)
        writer.write(b"show ip\r\n")
        await writer.drain()
        raw = await _drain_idle(reader, idle=0.4, total=_READ_TIMEOUT)
        if _parse_show_ip(raw.decode("utf-8", errors="replace"))["ip"]:
            return raw
    return raw


async def save_startup_config(host: str, port: int) -> tuple[bool, str]:
    """Persists a VPCS node's config to startup.vpc so a stop is recoverable."""
    try:
        async with console(host, port) as (reader, writer):
            writer.write(b"\r\n")
            await writer.drain()
            await asyncio.sleep(0.3)
            await _drain_idle(reader, idle=0.3, total=2.0)
            writer.write(b"save\r\n")
            await writer.drain()
            raw = await _drain_until_prompt(reader, timeout=_SAVE_TIMEOUT)
    except (TimeoutError, OSError) as exc:
        return False, f"connect failed: {exc}"
    text = raw.decode("utf-8", errors="replace")
    return bool(_SAVE_OK_RE.search(text)), text


async def _show_ip_once(host: str, port: int) -> tuple[dict, str]:
    """One connect-ask-parse cycle. Returns (parsed, log); parsed["ip"] is empty when unreadable."""
    async with console(host, port) as (reader, writer):
        writer.write(b"\r\n")
        await writer.drain()
        await asyncio.sleep(0.3)
        await _drain_idle(reader, idle=0.3, total=2.0)
        raw = await _read_show_ip(reader, writer)
    text = raw.decode("utf-8", errors="replace")
    return _parse_show_ip(text), text


async def read_show_ip(host: str, port: int) -> tuple[dict | None, str]:
    """Read `show ip` from a node, reconnecting while the console stays unreadable.

    Returns (parsed, log), or (None, log) when every attempt came back without an
    address. An unreadable console is a failure to observe, not a wrong answer, and
    callers must report it as such.
    """
    log = ""
    for attempt in range(_READ_ATTEMPTS):
        if attempt:
            await asyncio.sleep(_READ_BACKOFF * attempt)
        try:
            parsed, log = await _show_ip_once(host, port)
        except (TimeoutError, OSError) as exc:
            log = f"connect failed: {exc}"
            continue
        if parsed["ip"]:
            return parsed, log
    return None, log


async def vpcs_show_ip(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """Connects via telnet to the VPCS console and parses `show ip`."""
    node_name = params.get("node")
    if not node_name:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": "param 'node' missing"},
            log="",
        )

    port = ctx.node_console_port(node_name)
    if not port:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"node {node_name!r} not found or no console port"},
            log="",
        )
    host = ctx.node_console_host(node_name)

    parsed, log = await read_show_ip(host, port)
    if parsed is None:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={},
            log=log,
            observed=False,
            error_key="error.validation.console_unreadable",
            error_params={"node": node_name, "attempts": _READ_ATTEMPTS},
        )

    ok = parsed["ip"] == expect.get("ip") and parsed["gateway"] == expect.get("gateway")
    return CheckResult(ok=ok, expected=expect, actual=parsed, log=log)


def _parse_ping(text: str) -> dict:
    """Extract received / ttl from the output of the VPCS `ping` command.

    Each successful line has the form `N bytes from <addr> icmp_seq=K ttl=M time=...`.
    Returns `{received: int, ttl: int | None}`.
    """
    received = len(_PING_REPLY_RE.findall(text))
    ttls = _PING_TTL_RE.findall(text)
    return {"received": received, "ttl": int(ttls[-1]) if ttls else None}


def _matches(actual: int | None, expected) -> bool:
    """Compare a number against an expectation.

    `expected` can be an int or a string like `">=4"`, `"=5"`, `"5"`.
    """
    if actual is None:
        return False
    if isinstance(expected, int):
        return actual == expected
    if not isinstance(expected, str):
        return False
    m = _COMPARE_RE.match(expected)
    if not m:
        return False
    op = m.group(1) or "="
    target = int(m.group(2))
    return {
        "=": actual == target,
        "==": actual == target,
        ">=": actual >= target,
        "<=": actual <= target,
        ">": actual > target,
        "<": actual < target,
    }[op]


def _parse_show_ip(text: str) -> dict:
    """Extract ip and gateway from the output of the VPCS `show ip` command.

    `IP/MASK` has the form `192.168.10.10/24` (with prefix), `GATEWAY` is a bare address.
    Returns `{ip, gateway}` as strings; a missing field is an empty string.
    """
    ip_match = _IP_RE.search(text)
    gw_match = _GW_RE.search(text)
    return {
        "ip": ip_match.group(1) if ip_match else "",
        "gateway": gw_match.group(1) if gw_match else "",
    }


def _ip_in_subnet(ip_with_mask: str, subnet: str) -> bool:
    """True if the address from `IP/MASK` (or a bare address) belongs to CIDR `subnet`."""
    addr = ip_with_mask.split("/", 1)[0].strip()
    if not addr:
        return False
    try:
        return ipaddress.ip_address(addr) in ipaddress.ip_network(subnet, strict=False)
    except ValueError:
        return False


async def vpcs_ping(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """Send ICMP from a VPCS node and check received / ttl.

    params: `{from: PC1, to: "192.168.20.10"}`
    expect: `{received: ">=4"}` or `{received: 5, ttl: 62}`
    """
    src_name = params.get("from")
    target = params.get("to")
    if not src_name or not target:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": "params 'from' and 'to' are required"},
            log="",
        )

    port = ctx.node_console_port(src_name)
    if not port:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"node {src_name!r} not found or no console port"},
            log="",
        )
    host = ctx.node_console_host(src_name)

    try:
        async with console(host, port) as (reader, writer):
            writer.write(b"\r\n")
            await writer.drain()
            await asyncio.sleep(0.3)
            await _drain_idle(reader, idle=0.3, total=2.0)

            writer.write(f"ping {target}\r\n".encode())
            await writer.drain()
            await _drain_until_prompt(reader, timeout=_PING_READ_TIMEOUT)

            writer.write(f"ping {target}\r\n".encode())
            await writer.drain()
            raw = await _drain_until_prompt(reader, timeout=_PING_READ_TIMEOUT)
    except (TimeoutError, OSError) as exc:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"connect failed: {exc}"},
            log="",
        )

    text = raw.decode("utf-8", errors="replace")
    parsed = _parse_ping(text)
    if parsed["received"] == 0 and not _PING_UNREACHABLE_RE.search(text):
        return CheckResult(
            ok=False,
            expected=expect,
            actual={},
            log=text,
            observed=False,
            error_key="error.validation.console_unreadable",
            error_params={"node": src_name, "attempts": 1},
        )

    actual: dict = {"received": parsed["received"]}
    if parsed["ttl"] is not None:
        actual["ttl"] = parsed["ttl"]

    ok_received = _matches(parsed["received"], expect.get("received"))
    ok = ok_received
    if "ttl" in expect:
        ok = ok and _matches(parsed["ttl"], expect.get("ttl"))

    return CheckResult(ok=ok, expected=expect, actual=actual, log=text)


async def vpcs_ip_in_subnet(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """Connects via telnet to the VPCS console, parses `show ip`,
    and checks the address's subnet membership and gateway match.

    params: `{node: PC1}`
    expect: `{subnet: "192.168.10.0/24", gateway: "192.168.10.1"}`
    """
    node_name = params.get("node")
    if not node_name:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": "param 'node' missing"},
            log="",
        )

    port = ctx.node_console_port(node_name)
    if not port:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"node {node_name!r} not found or no console port"},
            log="",
        )
    host = ctx.node_console_host(node_name)

    parsed, log = await read_show_ip(host, port)
    if parsed is None:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={},
            log=log,
            observed=False,
            error_key="error.validation.console_unreadable",
            error_params={"node": node_name, "attempts": _READ_ATTEMPTS},
        )

    actual = {"ip": parsed["ip"], "gateway": parsed["gateway"]}
    subnet = expect.get("subnet", "")
    ok = _ip_in_subnet(parsed["ip"], subnet) and parsed["gateway"] == expect.get("gateway")
    return CheckResult(ok=ok, expected=expect, actual=actual, log=log)


async def vpcs_ping_node(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """Ping one VPCS node from another by reading the target's current address.

    params: `{from: PC1, to_node: PC2}`
    expect: `{received: ">=4"}`
    Used where the target address is assigned at runtime, as under DHCP.
    """
    target_name = params.get("to_node")
    if not target_name:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": "param 'to_node' missing"},
            log="",
        )

    target_port = ctx.node_console_port(target_name)
    if not target_port:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"node {target_name!r} not found or no console port"},
            log="",
        )

    parsed, log = await read_show_ip(ctx.node_console_host(target_name), target_port)
    if parsed is None:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={},
            log=log,
            observed=False,
            error_key="error.validation.console_unreadable",
            error_params={"node": target_name, "attempts": _READ_ATTEMPTS},
        )

    address = parsed["ip"].split("/", 1)[0].strip()
    if not address:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={},
            log=log,
            observed=False,
            error_key="error.validation.console_unreadable",
            error_params={"node": target_name, "attempts": _READ_ATTEMPTS},
        )

    return await vpcs_ping(ctx, {"from": params.get("from"), "to": address}, expect)
