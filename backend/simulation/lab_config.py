"""Консольные команды студента, выведенные ИЗ СПЕКИ лабы (не хардкод).

Детектор режимов кормится провалами spec-проверок (`LabProgressObserver` →
`check_failing`/`check_retry` как event_type=error). Чтобы сим порождал этот сигнал,
студент должен реально конфигурировать устройство в консоли: верная команда → проверка
проходит, неверная → падает. Эталон берём из `expect` самой спеки, поэтому конфиг
работает для любой VPCS-лабы без правок.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class NodeTask:
    """Что студент настраивает на конкретном узле."""

    node: str
    correct_cmd: str
    wrong_cmd: str


def _wrong_ip(ip_cidr: str) -> str:
    """Правдоподобная ошибка студента: тот же адрес, но чужая подсеть."""
    addr, _, prefix = ip_cidr.partition("/")
    octets = addr.split(".")
    if len(octets) != 4:
        return ip_cidr
    try:
        octets[2] = str((int(octets[2]) + 1) % 256)  # 192.168.1.11 → 192.168.2.11
    except ValueError:
        return ip_cidr
    wrong = ".".join(octets)
    return f"{wrong}/{prefix}" if prefix else wrong


def _static_task(node: str, expect: dict) -> NodeTask | None:
    """`vpcs.show_ip` — студент задаёт статический адрес вручную."""
    ip_cidr = expect.get("ip")
    if not ip_cidr:
        return None
    return NodeTask(
        node=node,
        correct_cmd=f"ip {ip_cidr}",
        wrong_cmd=f"ip {_wrong_ip(ip_cidr)}",
    )


def _dhcp_task(node: str, expect: dict) -> NodeTask | None:
    """`vpcs.ip_in_subnet` — адрес выдаёт DHCP: верно `ip dhcp`, ошибка — статика
    в чужой подсети (адрес есть, но проверка подсети падает)."""
    subnet = expect.get("subnet")
    if not subnet:
        return None
    net, _, prefix = subnet.partition("/")
    octets = net.split(".")
    if len(octets) != 4:
        return None
    try:
        octets[2] = str((int(octets[2]) + 1) % 256)
    except ValueError:
        return None
    wrong = ".".join(octets[:3] + ["50"])
    return NodeTask(
        node=node,
        correct_cmd="ip dhcp",
        wrong_cmd=f"ip {wrong}/{prefix or '24'}",
    )


_BUILDERS = {
    "vpcs.show_ip": _static_task,
    "vpcs.ip_in_subnet": _dhcp_task,
}


def build_node_tasks(spec: dict) -> list[NodeTask]:
    """Из spec-проверок → консольные команды студента (верная и ошибочная).

    Поддержаны оба способа адресации: статический (`vpcs.show_ip`) и DHCP
    (`vpcs.ip_in_subnet`). Проверки связности (`vpcs.ping`) задачи не дают —
    связность возникает как следствие правильной адресации.
    """
    tasks: list[NodeTask] = []
    seen: set[str] = set()
    for step in spec.get("steps", []):
        for check in step.get("checks", []):
            builder = _BUILDERS.get(check.get("kind"))
            node = check.get("node")
            if builder is None or not node or node in seen:
                continue
            task = builder(node, check.get("expect") or {})
            if task is None:
                continue
            seen.add(node)
            tasks.append(task)
    return tasks
