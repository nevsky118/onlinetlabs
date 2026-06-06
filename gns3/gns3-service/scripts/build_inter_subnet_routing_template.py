#!/usr/bin/env python3
"""Сборка шаблона лабы inter-subnet-routing в GNS3 v3 (шлюз на FRR).

R1 = FRR Router с FRR_ROLE=GW: два IP-шлюза, ip forwarding, без OSPF.
Печатает INTER_SUBNET_ROUTING_TEMPLATE_PROJECT_ID=<uuid>. Код выхода: 0 успех/уже есть, 2 нет шаблона FRR или ошибка API.
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import topology_builder as tb  # noqa: E402


GNS3_URL = os.environ.get("GNS3_URL", "http://localhost:3080")
GNS3_USER = os.environ.get("GNS3_ADMIN_USER", "admin")
GNS3_PASSWORD = os.environ.get("GNS3_ADMIN_PASSWORD", "admin")

PROJECT_NAME = "inter-subnet-routing-template"
ROUTER_TEMPLATE_NAME = "FRR Router"

PREFLIGHT_ERROR_MESSAGE = (
    "FRR Router template not registered in GNS3. "
    "Ensure gns3-service was restarted and gns3-server has /var/run/docker.sock mounted."
)


def _preflight(client: httpx.Client) -> str:
    templates = tb.list_templates(client)
    frr_id = tb.find_template_id(templates, ROUTER_TEMPLATE_NAME)
    if frr_id is None:
        sys.stderr.write(PREFLIGHT_ERROR_MESSAGE + "\n")
        raise SystemExit(2)
    return frr_id


def build_template(force: bool) -> str:
    client = httpx.Client(base_url=GNS3_URL, timeout=120)
    try:
        tb.authenticate(client, GNS3_USER, GNS3_PASSWORD)
        frr_template_id = _preflight(client)

        existing = tb.find_project_by_name(client, PROJECT_NAME)
        if existing and not force:
            return existing["project_id"]
        if existing and force:
            tb.delete_project(client, existing["project_id"])

        project_id = tb.create_project(client, PROJECT_NAME)

        r1 = tb.add_node_from_template(client, project_id, frr_template_id, x=0, y=0, rename="R1")
        tb.append_docker_env(client, project_id, r1, "FRR_ROLE=GW")
        tb.set_console_type(client, project_id, r1, "none")

        pc1 = tb.add_vpcs_node(client, project_id, name="PC1", x=-300, y=0)
        pc2 = tb.add_vpcs_node(client, project_id, name="PC2", x=300, y=0)

        # PC1 -> R1.eth0 (adapter 0): подсеть 192.168.1.0/24
        tb.link(client, project_id, pc1, 0, r1, 0, a_adapter=0, b_adapter=0)
        # PC2 -> R1.eth1 (adapter 1): подсеть 192.168.2.0/24
        tb.link(client, project_id, pc2, 0, r1, 0, a_adapter=0, b_adapter=1)

        return project_id
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the inter-subnet-routing FRR lab template in GNS3.")
    parser.add_argument("--force", action="store_true",
                        help="Delete the existing template project and rebuild.")
    args = parser.parse_args()
    try:
        project_id = build_template(force=args.force)
    except httpx.HTTPStatusError as exc:
        sys.stderr.write(f"GNS3 API error: {exc.response.status_code} {exc.response.text}\n")
        sys.exit(2)
    print(f"INTER_SUBNET_ROUTING_TEMPLATE_PROJECT_ID={project_id}")


if __name__ == "__main__":
    main()
