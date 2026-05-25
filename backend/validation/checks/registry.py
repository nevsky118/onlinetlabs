"""Реестр check-handlers: kind → async callable."""

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


@dataclass
class CheckResult:
    """Итог одной проверки: прошла ли, ожидаемые и фактические значения, лог консоли."""

    ok: bool
    expected: dict = field(default_factory=dict)
    actual: dict = field(default_factory=dict)
    log: str = ""


@dataclass
class CheckContext:
    """Сущности, доступные хендлерам во время прогона."""

    gns3_host: str
    nodes_by_name: dict  # name -> NodeState-like dict (console, console_host, status, ...)
    # gns3_project_id / frr_client заполняются для FRR-хендлеров;
    # vpcs.* хендлеры их не используют и могут получать пустые значения.
    gns3_project_id: str = ""
    frr_client: Any = None

    def node_console_port(self, name: str) -> int | None:
        """Вернуть порт консоли узла по имени. None, если узла нет."""
        node = self.nodes_by_name.get(name)
        if not node:
            return None
        return node.get("console")

    def node_console_host(self, name: str) -> str:
        """Вернуть хост консоли узла. Падает на gns3_host, если адрес пуст или непригоден."""
        node = self.nodes_by_name.get(name)
        if not node:
            return self.gns3_host
        host = node.get("console_host") or ""
        # GNS3 возвращает "0.0.0.0" как listening-адрес внутри контейнера —
        # для исходящих TCP-соединений это бесполезно. Падаем на gns3_host.
        if not host or host in ("0.0.0.0", "::"):
            return self.gns3_host
        return host

    def node_id(self, name: str) -> str | None:
        """Вернуть идентификатор узла по имени. None, если узла нет."""
        node = self.nodes_by_name.get(name)
        if not node:
            return None
        return node.get("id")


CheckHandler = Callable[[CheckContext, dict, dict], Awaitable[CheckResult]]

_REGISTRY: dict[str, CheckHandler] = {}
_BOOTSTRAPPED = False


def register(kind: str, handler: CheckHandler) -> None:
    """Привязать хендлер к виду проверки."""
    _REGISTRY[kind] = handler


def _bootstrap() -> None:
    """Регистрирует встроенные хендлеры. Идемпотентно, переносит риск
    циклического импорта на первый `get_handler`-вызов."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    import importlib

    vpcs = importlib.import_module("validation.checks.vpcs")
    frr = importlib.import_module("validation.checks.frr")
    cisco = importlib.import_module("validation.checks.cisco")

    register("vpcs.show_ip", vpcs.vpcs_show_ip)
    register("vpcs.ping", vpcs.vpcs_ping)
    register("frr.ospf_neighbor", frr.frr_ospf_neighbor)
    register("frr.route_in_table", frr.frr_route_in_table)
    register("cisco.ospf_neighbor", cisco.cisco_ospf_neighbor)
    register("cisco.route_in_table", cisco.cisco_route_in_table)
    register("cisco.interface_brief", cisco.cisco_interface_brief)
    _BOOTSTRAPPED = True


def get_handler(kind: str) -> CheckHandler | None:
    """Вернуть хендлер для вида проверки. None, если такого вида нет."""
    _bootstrap()
    return _REGISTRY.get(kind)
