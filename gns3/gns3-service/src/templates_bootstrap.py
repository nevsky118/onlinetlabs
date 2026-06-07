# Декларативная идемпотентная регистрация GNS3-шаблонов при старте gns3-service.
# Список — это данные; падение одного шаблона не блокирует старт (degraded mode).

import logging
from typing import Any

from src.gns3_admin_client import GNS3AdminClient

logger = logging.getLogger(__name__)


FRR_ROUTER_TEMPLATE = {
    "name": "FRR Router",
    "template_type": "docker",
    "compute_id": "local",
    "image": "onlinetlabs/frr-role:9.1.0",
    "adapters": 4,
    "start_command": "/sbin/tini -- /usr/lib/frr/docker-start",
    "console_type": "telnet",
    "console_resolution": "1024x768",
    "console_http_port": 80,
    "console_http_path": "/",
    "memory": 96,
    "category": "router",
    "symbol": ":/symbols/affinity/square/blue/router.svg",
    "default_name_format": "R{0}",
    # Демоны задаёт configs/daemons в образе; этот env — документация намерения, поведения не меняет.
    "environment": "FRR_ZEBRA=yes\nFRR_OSPFD=no",
    "usage": "Console: telnet to console port, then run `vtysh` for FRR CLI",
}

DHCP_SERVER_TEMPLATE = {
    "name": "DHCP Server",
    "template_type": "docker",
    "compute_id": "local",
    "image": "onlinetlabs/dhcp-role:latest",
    "adapters": 1,
    "console_type": "none",
    "memory": 48,
    "category": "guest",
    "symbol": ":/symbols/affinity/square/blue/server.svg",
    "default_name_format": "DHCP{0}",
    # dnsmasq читает эти env при старте; build-скрипт переопределяет под подсеть.
    "environment": (
        "DHCP_SUBNET=192.168.10.0/24\n"
        "DHCP_RANGE=192.168.10.100,192.168.10.200\n"
        "DHCP_GATEWAY=192.168.10.1"
    ),
    "usage": "Headless dnsmasq DHCP server. Configure via DHCP_* env vars.",
}


# Только узлы активных лаб: FRR (inter-subnet-routing) и DHCP (dhcp-basics).
# VPCS и ethernet_switch — встроенные узлы GNS3, отдельный шаблон не нужен.
LAB_TEMPLATES: list[dict[str, Any]] = [
    FRR_ROUTER_TEMPLATE,
    DHCP_SERVER_TEMPLATE,
]


async def ensure_lab_templates(admin: GNS3AdminClient) -> None:
    """Гарантировать наличие шаблонов из LAB_TEMPLATES в GNS3.

    Идемпотентно: для существующих по имени — пропуск. Ошибка одного
    шаблона логируется и не прерывает обработку остальных.
    """
    try:
        response = await admin.request("GET", "/v3/templates")
        response.raise_for_status()
        existing_names = {t.get("name") for t in response.json()}
    except Exception as exc:
        logger.error("Failed to list GNS3 templates, skip bootstrap: %s", exc)
        return

    for template in LAB_TEMPLATES:
        name = template["name"]
        if name in existing_names:
            logger.info("Template %r exists, skip", name)
            continue
        try:
            response = await admin.request("POST", "/v3/templates", json=template)
            response.raise_for_status()
            logger.info("Template %r created", name)
        except Exception as exc:
            logger.error("Failed to create template %r: %s", name, exc)
