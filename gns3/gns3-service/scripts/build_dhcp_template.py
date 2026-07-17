#!/usr/bin/env python3
"""Сборка шаблона лабы dhcp в GNS3 v3 (VPCS + коммутатор + DHCP-сервер).

Печатает DHCP_TEMPLATE_PROJECT_ID=<uuid>. Код выхода: 0 успех/уже есть, 2 нет шаблона DHCP или ошибка API.
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import topology_builder as tb

GNS3_URL = os.environ.get("GNS3_URL", "http://localhost:3080")
GNS3_USER = os.environ.get("GNS3_ADMIN_USER", "admin")
GNS3_PASSWORD = os.environ.get("GNS3_ADMIN_PASSWORD", "admin")

PROJECT_NAME = "dhcp-template"
DHCP_TEMPLATE_NAME = "DHCP Server"
SWITCH_SYMBOL = ":/symbols/affinity/square/blue/switch.svg"

PREFLIGHT_ERROR_MESSAGE = (
    "DHCP Server template not registered in GNS3. "
    "Ensure gns3-service was restarted (templates bootstrap registers it) "
    "and that gns3-server has /var/run/docker.sock mounted."
)


def _preflight(client: httpx.Client) -> str:
    templates = tb.list_templates(client)
    dhcp_id = tb.find_template_id(templates, DHCP_TEMPLATE_NAME)
    if dhcp_id is None:
        sys.stderr.write(PREFLIGHT_ERROR_MESSAGE + "\n")
        raise SystemExit(2)
    return dhcp_id


def build_template(force: bool) -> str:
    client = httpx.Client(base_url=GNS3_URL, timeout=120)
    try:
        tb.authenticate(client, GNS3_USER, GNS3_PASSWORD)
        dhcp_template_id = _preflight(client)

        existing = tb.find_project_by_name(client, PROJECT_NAME)
        if existing and not force:
            return existing["project_id"]
        if existing and force:
            tb.delete_project(client, existing["project_id"])

        project_id = tb.create_project(client, PROJECT_NAME)

        sw1 = tb.add_raw_node(
            client,
            project_id,
            name="SW1",
            node_type="ethernet_switch",
            x=0,
            y=0,
            symbol=SWITCH_SYMBOL,
        )
        pc1 = tb.add_vpcs_node(client, project_id, name="PC1", x=-200, y=-150)
        pc2 = tb.add_vpcs_node(client, project_id, name="PC2", x=200, y=-150)

        dhcp = tb.add_node_from_template(
            client,
            project_id,
            dhcp_template_id,
            x=0,
            y=200,
            rename="DHCP",
        )
        tb.append_docker_env(client, project_id, dhcp, "DHCP_SUBNET=192.168.10.0/24")
        tb.append_docker_env(client, project_id, dhcp, "DHCP_RANGE=192.168.10.100,192.168.10.200")
        tb.append_docker_env(client, project_id, dhcp, "DHCP_GATEWAY=192.168.10.1")
        # Headless: telnet-консоль через WS падает на Docker Desktop macOS.
        tb.set_console_type(client, project_id, dhcp, "none")

        tb.link(client, project_id, pc1, 0, sw1, 0, a_adapter=0, b_adapter=0)
        tb.link(client, project_id, pc2, 0, sw1, 1, a_adapter=0, b_adapter=0)
        tb.link(client, project_id, dhcp, 0, sw1, 2, a_adapter=0, b_adapter=0)

        return project_id
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the dhcp lab template in GNS3.")
    parser.add_argument(
        "--force", action="store_true", help="Delete the existing template project and rebuild."
    )
    args = parser.parse_args()
    try:
        project_id = build_template(force=args.force)
    except httpx.HTTPStatusError as exc:
        sys.stderr.write(f"GNS3 API error: {exc.response.status_code} {exc.response.text}\n")
        sys.exit(2)
    print(f"DHCP_TEMPLATE_PROJECT_ID={project_id}")


if __name__ == "__main__":
    main()
