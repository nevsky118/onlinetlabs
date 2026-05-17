#!/usr/bin/env python3
"""Build the ospf-vlan lab template project in GNS3 v3 (FRR + builtin switches).

Topology — same shape as the lite and IOSvL2 variants, but routers are
FRRouting (Docker) and switches are builtin GNS3 ethernet_switch with VLANs
preconfigured in the template:

    PC1 - e0 - Eth0 SW1 Eth2 - eth0 R1 eth1 - eth1 R2 eth0 - Eth2 SW2 Eth0 - e0 PC3
    PC2 - e0 - Eth1 SW1                                             SW2 Eth1 - e0 PC4

Switch port VLAN mapping (identical on SW1 and SW2, identical to lite variant):
    Eth0 -> access vlan 10
    Eth1 -> access vlan 20
    Eth2 -> dot1q trunk (carries 10 + 20)

R1, R2:    "FRR Router" template (docker, FRRouting 9.1.0). Interfaces eth0..eth3,
           ports are (adapter_number=N, port_number=0).
SW1, SW2:  builtin ethernet_switch (same as lite).
PC1..PC4:  builtin VPCS (same as lite).

CLI:
    python build_frr_lab_template.py            # idempotent: existing -> print UUID, exit 0
    python build_frr_lab_template.py --force    # delete existing and rebuild

On success prints exactly one line to stdout:
    FRR_TEMPLATE_PROJECT_ID=<uuid>

Exit codes:
    0  success or existing project found (no --force)
    2  preflight failed: FRR Router template missing, or GNS3 API error
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

PROJECT_NAME = "ospf-vlan-template-frr"

ROUTER_TEMPLATE_NAME = "FRR Router"

PREFLIGHT_ERROR_MESSAGE = (
    "FRR Router template not registered in GNS3. "
    "Ensure gns3-service was restarted (templates bootstrap registers it) "
    "and that gns3-server has /var/run/docker.sock mounted."
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

        # 4-нодовая топология ради масштаба (50 одновременных сессий):
        #   PC1 — eth0 R1 eth1 ═══ eth1 R2 eth0 — PC3
        # R1/R2 авто-настраиваются по FRR_ROLE (плоский site-IP на eth0,
        # backbone на eth1, OSPF area 0). Свитчи и VLAN убраны.
        r1 = tb.add_node_from_template(client, project_id, frr_template_id, x=-200, y=0, rename="R1")
        tb.append_docker_env(client, project_id, r1, "FRR_ROLE=R1")
        tb.set_console_type(client, project_id, r1, "none")
        r2 = tb.add_node_from_template(client, project_id, frr_template_id, x=200, y=0, rename="R2")
        tb.append_docker_env(client, project_id, r2, "FRR_ROLE=R2")
        tb.set_console_type(client, project_id, r2, "none")

        pc1 = tb.add_vpcs_node(client, project_id, name="PC1", x=-400, y=0)
        pc3 = tb.add_vpcs_node(client, project_id, name="PC3", x=400, y=0)

        # FRR docker узлы: eth0 = adapter 0, eth1 = adapter 1.
        # PC1 — R1.eth0 (site A).
        tb.link(client, project_id, pc1, 0, r1, 0, a_adapter=0, b_adapter=0)
        # Backbone R1.eth1 ═══ R2.eth1.
        tb.link(client, project_id, r1, 0, r2, 0, a_adapter=1, b_adapter=1)
        # PC3 — R2.eth0 (site B).
        tb.link(client, project_id, pc3, 0, r2, 0, a_adapter=0, b_adapter=0)

        return project_id
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the ospf-vlan FRR lab template in GNS3."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete the existing template project and rebuild from scratch.",
    )
    args = parser.parse_args()

    try:
        project_id = build_template(force=args.force)
    except httpx.HTTPStatusError as exc:
        sys.stderr.write(f"GNS3 API error: {exc.response.status_code} {exc.response.text}\n")
        sys.exit(2)

    print(f"FRR_TEMPLATE_PROJECT_ID={project_id}")


if __name__ == "__main__":
    main()
