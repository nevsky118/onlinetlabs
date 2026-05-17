# Декларативная регистрация GNS3-шаблонов при старте gns3-service.
#
# Принцип: приложение само поднимает свои инфра-зависимости. Список шаблонов
# описан тут как данные; ensure-loop идемпотентен — повторный запуск не дубль.
# Падение одного шаблона не блокирует загрузку приложения (degraded mode).

import logging
from typing import Any

from src.gns3_admin_client import GNS3AdminClient

logger = logging.getLogger(__name__)


async def _image_present(admin: GNS3AdminClient, filename: str) -> bool:
    try:
        response = await admin.request("GET", "/v3/images?image_type=qemu")
        response.raise_for_status()
        images = response.json()
        return any(img.get("filename") == filename for img in images)
    except Exception as exc:
        logger.warning("Failed to list QEMU images, skip presence check: %s", exc)
        return False


CISCO_IOSV_TEMPLATE = {
    "name": "Cisco IOSv",
    "template_type": "qemu",
    "compute_id": "local",
    "category": "router",
    "symbol": ":/symbols/affinity/square/blue/router.svg",
    "default_name_format": "R{0}",
    "port_name_format": "Gi0/{0}",
    "qemu_path": "/usr/bin/qemu-system-x86_64",
    "adapter_type": "e1000",
    "adapters": 4,
    "ram": 512,
    "console_type": "telnet",
    "kvm": "require",
    "hda_disk_interface": "virtio",
    "hda_disk_image": "vios-adventerprisek9-m.spa.159-3.m10.qcow2",
}

CISCO_IOSVL2_TEMPLATE = {
    "name": "Cisco IOSvL2",
    "template_type": "qemu",
    "compute_id": "local",
    "category": "multilayer_switch",
    "symbol": ":/symbols/affinity/square/blue/switch_multilayer.svg",
    "default_name_format": "SW{0}",
    "port_name_format": "Gi{1}/{0}",
    "port_segment_size": 4,
    "qemu_path": "/usr/bin/qemu-system-x86_64",
    "adapter_type": "e1000",
    "adapters": 16,
    "ram": 768,
    "console_type": "telnet",
    "kvm": "require",
    "hda_disk_interface": "virtio",
    "hda_disk_image": "vios_l2-adventerprisek9-m.ssa.high_iron_20200929.qcow2",
}

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
    "memory": 128,
    "category": "router",
    "symbol": ":/symbols/affinity/square/blue/router.svg",
    "default_name_format": "R{0}",
    # Демоны включаются файлом /etc/frr/daemons в образе onlinetlabs/frr-role
    # (см. gns3/frr-role/configs/daemons: zebra=yes, ospfd=yes, остальные =no).
    # Переменные FRR_* читает только upstream-скрипт docker-start; раз daemons-файл
    # уже задан в образе, env реально ничего не меняет. Оставляем только
    # zebra+ospfd как документацию намерения — синхронно с daemons-файлом.
    # Если нужно включить новый демон — правь configs/daemons и пересобирай образ.
    "environment": "FRR_ZEBRA=yes\nFRR_OSPFD=yes",
    "usage": "Console: telnet to console port, then run `vtysh` for FRR CLI",
}


LAB_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "Cisco c3745",
        "template_type": "dynamips",
        "compute_id": "local",
        "platform": "c3745",
        "image": "c3745-adventerprisek9-mz.124-25d.image",
        "ram": 256,
        "nvram": 256,
        "iomem": 5,
        "exec_area": 64,
        "mmap": True,
        "sparsemem": True,
        "idlepc": "0x60aa1dbc",
        "slot0": "GT96100-FE",
        "symbol": ":/symbols/affinity/square/blue/router.svg",
        "category": "router",
        "default_name_format": "R{0}",
    },
    CISCO_IOSV_TEMPLATE,
    CISCO_IOSVL2_TEMPLATE,
    FRR_ROUTER_TEMPLATE,
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
        image = template.get("hda_disk_image")
        if image and template.get("template_type") == "qemu":
            if not await _image_present(admin, image):
                logger.info(
                    "Image %r not present, skip QEMU template %r", image, name
                )
                continue
        try:
            response = await admin.request("POST", "/v3/templates", json=template)
            response.raise_for_status()
            logger.info("Template %r created", name)
        except Exception as exc:
            logger.error("Failed to create template %r: %s", name, exc)
