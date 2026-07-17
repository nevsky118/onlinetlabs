"""Student console commands derived FROM THE LAB SPEC (not hardcoded).

The regime detector is fed by spec-check failures (`LabProgressObserver` →
`check_failing`/`check_retry` as event_type=error). For the sim to produce this
signal, the student must actually configure the device in the console: correct
command → check passes, wrong → fails. The reference comes from the spec's own
`expect`, so the config works for any VPCS lab without changes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeTask:
    """What the student configures on a specific node."""

    node: str
    correct_cmd: str
    wrong_cmd: str


def _wrong_ip(ip_cidr: str) -> str:
    """A plausible student mistake: same address, wrong subnet."""
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
    """`vpcs.show_ip`: student sets a static address manually."""
    ip_cidr = expect.get("ip")
    if not ip_cidr:
        return None
    return NodeTask(
        node=node,
        correct_cmd=f"ip {ip_cidr}",
        wrong_cmd=f"ip {_wrong_ip(ip_cidr)}",
    )


def _dhcp_task(node: str, expect: dict) -> NodeTask | None:
    """`vpcs.ip_in_subnet`: DHCP assigns the address, correct is `ip dhcp`. The mistake
    is a static address in the wrong subnet (address present, but the subnet check fails)."""
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
    """From spec checks → student console commands (correct and wrong).

    Both addressing modes are supported: static (`vpcs.show_ip`) and DHCP
    (`vpcs.ip_in_subnet`). Connectivity checks (`vpcs.ping`) don't produce a task,
    connectivity follows as a consequence of correct addressing.
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
