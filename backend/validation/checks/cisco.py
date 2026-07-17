"""Cisco IOS check-handlers — `cisco.ospf_neighbor`, `cisco.route_in_table`,
`cisco.interface_brief`.

Хендлеры подключаются telnet'ом к dynamips-консоли узла и выполняют
`show ...` команды. Парсинг живёт в чистых функциях
`_parse_cisco_neighbor` / `_parse_cisco_route` / `_parse_cisco_interface`,
чтобы их можно было покрыть unit-тестами без сетевых вызовов.
"""

from __future__ import annotations

import asyncio
import re

from validation.checks.registry import CheckContext, CheckResult


# `2.2.2.2           1   FULL/BDR        00:00:32    10.0.0.2  FastEthernet0/1`
_CISCO_NEIGHBOR_LINE_RE = re.compile(r"^\s*(\S+)\s+\d+\s+(\S+)")

# `O    192.168.110.0/24 [110/20] via 10.0.0.2, FastEthernet0/1`
# code часть — буквы и `*`, не цифры (отбрасываем сами заголовки "Codes:" и т.п.).
_CISCO_ROUTE_LINE_RE = re.compile(r"^\s*([A-Z][A-Z*]*)\s+(\d+\.\d+\.\d+\.\d+/\d+)\b")

# `FastEthernet0/0.10  192.168.10.1    YES manual up                    up`
_CISCO_IFACE_LINE_RE = re.compile(r"^\s*(\S+)\s+(\S+)\s+\S+\s+\S+\s+(\S+(?:\s+\S+)?)\s+(\S+)\s*$")

_CONNECT_TIMEOUT = 5.0
_READ_TIMEOUT = 6.0
_PROMPT_TAIL = b"#"


def _parse_cisco_neighbor(stdout: str, neighbor_id: str) -> str | None:
    """Вернуть значение колонки State (например `FULL/BDR`) для соседа.

    Возвращает None, если соседа нет в выводе.
    """
    for raw_line in stdout.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        stripped = line.lstrip()
        if stripped.startswith("Neighbor ID"):
            continue
        m = _CISCO_NEIGHBOR_LINE_RE.match(line)
        if not m:
            continue
        if m.group(1) == neighbor_id:
            return m.group(2)
    return None


def _parse_cisco_route(stdout: str, prefix: str) -> tuple[str, str] | None:
    """Вернуть `(code, full_line)` маршрута с заданным префиксом.

    code — первая колонка, напр. `O` или `O*E2`. None, если префикс не найден.
    """
    for raw_line in stdout.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        stripped = line.lstrip()
        # `Codes: ...` шапка и подобный текст матчатся первой группой,
        # но второй группы (префикса) у них нет — re.match даст None или
        # mismatch по prefix. Дополнительно отсечь явные header-строки.
        if stripped.startswith(("Codes:", "Gateway of last resort")):
            continue
        m = _CISCO_ROUTE_LINE_RE.match(line)
        if not m:
            continue
        if m.group(2) == prefix:
            return m.group(1), line.strip()
    return None


def _parse_cisco_interface(stdout: str, interface: str) -> dict | None:
    """Вернуть `{ip, status, protocol}` строки `show ip interface brief`.

    None, если интерфейс не найден.
    """
    for raw_line in stdout.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        # Первая колонка — имя. Сравниваем строго.
        # Формат строки фиксированный: <name> <ip> <ok-method-2cols> <status> <protocol>.
        parts = line.split()
        if len(parts) < 6:
            continue
        if parts[0] != interface:
            continue
        # parts: [name, ip, ok, method, status, protocol]
        # Status может быть `administratively down` (2 слова) — разрулим.
        # Попробуем формат с 6 полями, если status = одно слово.
        if len(parts) == 6:
            return {
                "interface": parts[0],
                "ip": parts[1],
                "status": parts[4],
                "protocol": parts[5],
            }
        if len(parts) == 7:
            # `administratively down` — двусловный статус.
            return {
                "interface": parts[0],
                "ip": parts[1],
                "status": f"{parts[4]} {parts[5]}",
                "protocol": parts[6],
            }
        # fallback — отдадим что нашли.
        return {
            "interface": parts[0],
            "ip": parts[1],
            "status": parts[-2],
            "protocol": parts[-1],
        }
    return None


def _missing_param(name: str, expect: dict) -> CheckResult:
    """Сформировать проваленный результат об отсутствующем параметре."""
    return CheckResult(
        ok=False,
        expected=expect,
        actual={"error": f"param {name!r} missing"},
        log="",
    )


async def _drain_until_prompt(reader: asyncio.StreamReader, timeout: float) -> bytes:
    """Читать с консоли пока не встретится Cisco-приглашение (# или >) или истечёт таймаут."""
    buf = bytearray()
    try:
        async with asyncio.timeout(timeout):
            while True:
                chunk = await reader.read(1024)
                if not chunk:
                    break
                buf.extend(chunk)
                # Cisco prompt оканчивается на `#` (privileged) или `>` (user).
                # Достаточно проверить хвост последней строки.
                tail = buf[-3:]
                if _PROMPT_TAIL in tail or b"> " in tail or b">" == tail[-1:]:
                    # Дать ещё чуть-чуть подтянуть остаток.
                    await asyncio.sleep(0.1)
                    while True:
                        try:
                            async with asyncio.timeout(0.2):
                                more = await reader.read(1024)
                        except (asyncio.TimeoutError, TimeoutError):
                            break
                        if not more:
                            break
                        buf.extend(more)
                    break
    except (asyncio.TimeoutError, TimeoutError):
        pass
    return bytes(buf)


async def _exec_cisco(
    ctx: CheckContext, node_name: str, command: str, expect: dict
) -> tuple[str | None, CheckResult | None]:
    """Подключиться к консоли узла, отключить пагинатор и выполнить команду.

    Возвращает `(stdout_text, None)` при успехе, `(None, error_result)` иначе.
    """
    port = ctx.node_console_port(node_name)
    if not port:
        return None, CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"node {node_name!r} not found or no console port"},
            log="",
        )
    host = ctx.node_console_host(node_name)

    try:
        async with asyncio.timeout(_CONNECT_TIMEOUT):
            reader, writer = await asyncio.open_connection(host, port)
    except (asyncio.TimeoutError, TimeoutError, OSError) as exc:
        return None, CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"connect failed: {exc}"},
            log="",
        )

    try:
        # Разбудить консоль.
        writer.write(b"\r\n")
        await writer.drain()
        await asyncio.sleep(0.3)
        await _drain_until_prompt(reader, timeout=1.0)

        # Войти в enable (у dynamips обычно без пароля).
        writer.write(b"enable\r\n")
        await writer.drain()
        await _drain_until_prompt(reader, timeout=1.5)

        # Отключить пагинатор.
        writer.write(b"terminal length 0\r\n")
        await writer.drain()
        await _drain_until_prompt(reader, timeout=1.5)

        # Сама команда.
        writer.write(command.encode() + b"\r\n")
        await writer.drain()
        raw = await _drain_until_prompt(reader, timeout=_READ_TIMEOUT)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    return raw.decode("utf-8", errors="replace"), None


async def cisco_ospf_neighbor(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """`show ip ospf neighbor` → проверка state конкретного соседа.

    params: `{node: "R1"}`
    expect: `{neighbor_id: "2.2.2.2", state: "FULL"}`
            Сравнение state через `startswith`, так что `FULL` покрывает
            `FULL/BDR`, `FULL/DR`, `FULL/DROTHER`.
    """
    node_name = params.get("node")
    if not node_name:
        return _missing_param("node", expect)
    neighbor_id = expect.get("neighbor_id")
    expected_state = expect.get("state")
    if not neighbor_id or not expected_state:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": "expect must contain 'neighbor_id' and 'state'"},
            log="",
        )

    stdout, err = await _exec_cisco(ctx, node_name, "show ip ospf neighbor", expect)
    if err is not None:
        return err

    state = _parse_cisco_neighbor(stdout or "", neighbor_id)
    actual = {"neighbor_id": neighbor_id, "state": state}
    ok = state is not None and state.upper().startswith(expected_state.upper())
    return CheckResult(ok=ok, expected=expect, actual=actual, log=stdout or "")


async def cisco_route_in_table(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """`show ip route ospf` → проверка наличия маршрута с нужным protocol-кодом.

    params: `{node: "R1"}`
    expect: `{prefix: "192.168.110.0/24", protocol: "O"}`
            Сравнение protocol через `startswith` → `O` покрывает `O*E2` и пр.
    """
    node_name = params.get("node")
    if not node_name:
        return _missing_param("node", expect)
    prefix = expect.get("prefix")
    protocol = expect.get("protocol")
    if not prefix or not protocol:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": "expect must contain 'prefix' and 'protocol'"},
            log="",
        )

    stdout, err = await _exec_cisco(ctx, node_name, "show ip route ospf", expect)
    if err is not None:
        return err

    parsed = _parse_cisco_route(stdout or "", prefix)
    actual = {
        "prefix": prefix,
        "protocol": parsed[0] if parsed else None,
        "route": parsed[1] if parsed else None,
    }
    ok = parsed is not None and parsed[0].startswith(protocol)
    return CheckResult(ok=ok, expected=expect, actual=actual, log=stdout or "")


async def cisco_interface_brief(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """`show ip interface brief` → проверка IP/status конкретного интерфейса.

    params: `{node: "R1", interface: "FastEthernet0/0.10"}`
    expect: `{status: "up", ip: "192.168.10.1"}` — `ip` опционален.
    """
    node_name = params.get("node")
    interface = params.get("interface")
    if not node_name:
        return _missing_param("node", expect)
    if not interface:
        return _missing_param("interface", expect)

    stdout, err = await _exec_cisco(ctx, node_name, "show ip interface brief", expect)
    if err is not None:
        return err

    parsed = _parse_cisco_interface(stdout or "", interface)
    if parsed is None:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"interface {interface!r} not found"},
            log=stdout or "",
        )

    actual = {"ip": parsed["ip"], "status": parsed["status"]}
    expected_status = expect.get("status")
    expected_ip = expect.get("ip")
    ok = True
    if expected_status:
        ok = ok and actual["status"].lower() == expected_status.lower()
    if expected_ip:
        ok = ok and actual["ip"] == expected_ip
    return CheckResult(ok=ok, expected=expect, actual=actual, log=stdout or "")
