"""VPCS check-handlers — `vpcs.show_ip`, `vpcs.ping`."""

import asyncio
import ipaddress
import re

from validation.checks.registry import CheckContext, CheckResult

_IP_RE = re.compile(r"IP/MASK\s*:\s*(\S+)", re.IGNORECASE)
_GW_RE = re.compile(r"GATEWAY\s*:\s*(\S+)", re.IGNORECASE)

# Каждая успешная строка ответа VPCS-ping выглядит как:
#   `84 bytes from 192.168.20.10 icmp_seq=1 ttl=62 time=2.345 ms`
_PING_REPLY_RE = re.compile(r"^\s*\d+\s+bytes\s+from\s+\S+", re.MULTILINE)
_PING_TTL_RE = re.compile(r"\bttl=(\d+)", re.IGNORECASE)
# `>=N` / `>N` / `==N` / `=N` / `N`. По умолчанию строгое равенство.
_COMPARE_RE = re.compile(r"^\s*(>=|<=|==|=|>|<)?\s*(\d+)\s*$")

_CONNECT_TIMEOUT = 5.0
_READ_TIMEOUT = 3.0
_PING_READ_TIMEOUT = 8.0
_PROMPT = b"> "


async def _drain_until_prompt(reader: asyncio.StreamReader, timeout: float) -> bytes:
    """Читать с консоли пока не встретится VPCS-приглашение или истечёт таймаут."""
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


async def vpcs_show_ip(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """Подключается telnet'ом к VPCS-консоли, парсит `show ip`."""
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

    try:
        async with asyncio.timeout(_CONNECT_TIMEOUT):
            reader, writer = await asyncio.open_connection(host, port)
    except (TimeoutError, OSError) as exc:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"connect failed: {exc}"},
            log="",
        )

    try:
        writer.write(b"\r\n")
        await writer.drain()
        await asyncio.sleep(0.3)
        # Стряхиваем накопленный prompt/echo.
        await _drain_until_prompt(reader, timeout=0.5)

        writer.write(b"show ip\r\n")
        await writer.drain()

        raw = await _drain_until_prompt(reader, timeout=_READ_TIMEOUT)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    text = raw.decode("utf-8", errors="replace")
    ip_match = _IP_RE.search(text)
    gw_match = _GW_RE.search(text)
    actual = {
        "ip": ip_match.group(1) if ip_match else "",
        "gateway": gw_match.group(1) if gw_match else "",
    }
    ok = actual["ip"] == expect.get("ip") and actual["gateway"] == expect.get("gateway")
    return CheckResult(ok=ok, expected=expect, actual=actual, log=text)


def _parse_ping(text: str) -> dict:
    """Извлечь received / ttl из вывода VPCS-команды `ping`.

    Каждая успешная строка имеет вид `N bytes from <addr> icmp_seq=K ttl=M time=...`.
    Возвращает `{received: int, ttl: int | None}`.
    """
    received = len(_PING_REPLY_RE.findall(text))
    ttls = _PING_TTL_RE.findall(text)
    return {"received": received, "ttl": int(ttls[-1]) if ttls else None}


def _matches(actual: int | None, expected) -> bool:
    """Сравнить число с ожиданием.

    `expected` может быть int или строкой типа `">=4"`, `"=5"`, `"5"`.
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
    """Извлечь ip и gateway из вывода VPCS-команды `show ip`.

    `IP/MASK` имеет вид `192.168.10.10/24` (с префиксом), `GATEWAY` — голый адрес.
    Возвращает `{ip, gateway}` со строками; отсутствующее поле — пустая строка.
    """
    ip_match = _IP_RE.search(text)
    gw_match = _GW_RE.search(text)
    return {
        "ip": ip_match.group(1) if ip_match else "",
        "gateway": gw_match.group(1) if gw_match else "",
    }


def _ip_in_subnet(ip_with_mask: str, subnet: str) -> bool:
    """True, если адрес из `IP/MASK` (или голый адрес) принадлежит CIDR `subnet`."""
    addr = ip_with_mask.split("/", 1)[0].strip()
    if not addr:
        return False
    try:
        return ipaddress.ip_address(addr) in ipaddress.ip_network(subnet, strict=False)
    except ValueError:
        return False


async def vpcs_ping(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """Отправить ICMP с VPCS-узла и проверить received / ttl.

    params: `{from: PC1, to: "192.168.20.10"}`
    expect: `{received: ">=4"}` или `{received: 5, ttl: 62}`
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
        async with asyncio.timeout(_CONNECT_TIMEOUT):
            reader, writer = await asyncio.open_connection(host, port)
    except (TimeoutError, OSError) as exc:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"connect failed: {exc}"},
            log="",
        )

    try:
        writer.write(b"\r\n")
        await writer.drain()
        await asyncio.sleep(0.3)
        await _drain_until_prompt(reader, timeout=0.5)

        writer.write(f"ping {target}\r\n".encode())
        await writer.drain()

        raw = await _drain_until_prompt(reader, timeout=_PING_READ_TIMEOUT)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    text = raw.decode("utf-8", errors="replace")
    parsed = _parse_ping(text)

    actual: dict = {"received": parsed["received"]}
    if parsed["ttl"] is not None:
        actual["ttl"] = parsed["ttl"]

    ok_received = _matches(parsed["received"], expect.get("received"))
    ok = ok_received
    if "ttl" in expect:
        ok = ok and _matches(parsed["ttl"], expect.get("ttl"))

    return CheckResult(ok=ok, expected=expect, actual=actual, log=text)


async def vpcs_ip_in_subnet(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """Подключается telnet'ом к VPCS-консоли, парсит `show ip`,
    проверяет принадлежность адреса подсети и совпадение шлюза.

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

    try:
        async with asyncio.timeout(_CONNECT_TIMEOUT):
            reader, writer = await asyncio.open_connection(host, port)
    except (TimeoutError, OSError) as exc:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"connect failed: {exc}"},
            log="",
        )

    try:
        writer.write(b"\r\n")
        await writer.drain()
        await asyncio.sleep(0.3)
        await _drain_until_prompt(reader, timeout=0.5)

        writer.write(b"show ip\r\n")
        await writer.drain()

        raw = await _drain_until_prompt(reader, timeout=_READ_TIMEOUT)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    text = raw.decode("utf-8", errors="replace")
    parsed = _parse_show_ip(text)
    actual = {"ip": parsed["ip"], "gateway": parsed["gateway"]}

    subnet = expect.get("subnet", "")
    ok = _ip_in_subnet(parsed["ip"], subnet) and parsed["gateway"] == expect.get("gateway")
    return CheckResult(ok=ok, expected=expect, actual=actual, log=text)
