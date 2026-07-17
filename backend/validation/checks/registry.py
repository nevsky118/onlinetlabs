"""Registry of check handlers: kind -> async callable."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckResult:
    """Outcome of a single check: pass/fail, expected and actual values, console log."""

    ok: bool
    expected: dict = field(default_factory=dict)
    actual: dict = field(default_factory=dict)
    log: str = ""


@dataclass
class CheckContext:
    """Entities available to handlers during a run."""

    gns3_host: str
    nodes_by_name: dict  # name -> NodeState-like dict (console, console_host, status, ...)
    # gns3_project_id / frr_client are populated for FRR handlers;
    # vpcs.* handlers don't use them and may receive empty values.
    gns3_project_id: str = ""
    frr_client: Any = None

    def node_console_port(self, name: str) -> int | None:
        """Return the node's console port by name. None if the node doesn't exist."""
        node = self.nodes_by_name.get(name)
        if not node:
            return None
        return node.get("console")

    def node_console_host(self, name: str) -> str:
        """Return the node's console host. Falls back to gns3_host if the address is empty or unusable."""
        node = self.nodes_by_name.get(name)
        if not node:
            return self.gns3_host
        host = node.get("console_host") or ""
        # GNS3 returns "0.0.0.0" as the listening address inside the container —
        # useless for outbound TCP connections. Fall back to gns3_host.
        if not host or host in ("0.0.0.0", "::"):
            return self.gns3_host
        return host

    def node_id(self, name: str) -> str | None:
        """Return the node's id by name. None if the node doesn't exist."""
        node = self.nodes_by_name.get(name)
        if not node:
            return None
        return node.get("id")


CheckHandler = Callable[[CheckContext, dict, dict], Awaitable[CheckResult]]

_REGISTRY: dict[str, CheckHandler] = {}
_BOOTSTRAPPED = False


def register(kind: str, handler: CheckHandler) -> None:
    """Bind a handler to a check kind."""
    _REGISTRY[kind] = handler


def _bootstrap() -> None:
    """Registers the built-in handlers. Idempotent, defers the risk of a
    circular import to the first `get_handler` call."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    import importlib

    vpcs = importlib.import_module("validation.checks.vpcs")
    frr = importlib.import_module("validation.checks.frr")
    cisco = importlib.import_module("validation.checks.cisco")

    register("vpcs.show_ip", vpcs.vpcs_show_ip)
    register("vpcs.ping", vpcs.vpcs_ping)
    register("vpcs.ip_in_subnet", vpcs.vpcs_ip_in_subnet)
    register("frr.ospf_neighbor", frr.frr_ospf_neighbor)
    register("frr.route_in_table", frr.frr_route_in_table)
    register("cisco.ospf_neighbor", cisco.cisco_ospf_neighbor)
    register("cisco.route_in_table", cisco.cisco_route_in_table)
    register("cisco.interface_brief", cisco.cisco_interface_brief)
    _BOOTSTRAPPED = True


def get_handler(kind: str) -> CheckHandler | None:
    """Return the handler for a check kind. None if no such kind exists."""
    _bootstrap()
    return _REGISTRY.get(kind)
