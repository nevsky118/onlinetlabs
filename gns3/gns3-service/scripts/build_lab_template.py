#!/usr/bin/env python3
"""Build the ospf-vlan lab template project in GNS3 v3.

Builds a deterministic 8-node topology used to clone per-session lab projects:

    PC1 - e0 - Eth0 SW1 Eth2 - f0/0 R1 f0/1 - f0/1 R2 f0/0 - Eth2 SW2 Eth0 - e0 PC3
    PC2 - e0 - Eth1 SW1                                             SW2 Eth1 - e0 PC4

Switch port VLAN mapping (identical on SW1 and SW2):
    Eth0 -> access vlan 10
    Eth1 -> access vlan 20
    Eth2 -> dot1q trunk (carries 10 + 20)
    Eth3..7 left untouched (default access vlan 1)

R1 / R2 do router-on-a-stick on f0/0 (configured by student); switches tag in hardware.

CLI:
    python build_lab_template.py            # idempotent: existing project -> print UUID, exit 0
    python build_lab_template.py --force    # delete existing and rebuild

On success prints exactly one line to stdout:
    TEMPLATE_PROJECT_ID=<uuid>
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

# Позволяет запускать как `python scripts/build_lab_template.py` без -m.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import topology_builder as tb

GNS3_URL = os.environ.get("GNS3_URL", "http://localhost:3080")
GNS3_USER = os.environ.get("GNS3_ADMIN_USER", "admin")
GNS3_PASSWORD = os.environ.get("GNS3_ADMIN_PASSWORD", "admin")
TEMPLATE_NAME = "ospf-vlan-template"

ROUTER_TEMPLATE_NAME = "Cisco c3745"

# Cisco c3745 NIC port numbering on slot 0 (GT96100-FE).
ROUTER_F00_PORT = 0  # f0/0
ROUTER_F01_PORT = 1  # f0/1


def build_template(force: bool) -> str:
    client = httpx.Client(base_url=GNS3_URL, timeout=60)
    try:
        tb.authenticate(client, GNS3_USER, GNS3_PASSWORD)

        existing = tb.find_project_by_name(client, TEMPLATE_NAME)
        if existing and not force:
            return existing["project_id"]
        if existing and force:
            tb.delete_project(client, existing["project_id"])

        templates = tb.list_templates(client)
        c3745_template_id = tb.find_template_id(templates, ROUTER_TEMPLATE_NAME)
        if c3745_template_id is None:
            raise SystemExit(f"GNS3 template not found by name: {ROUTER_TEMPLATE_NAME!r}")

        project_id = tb.create_project(client, TEMPLATE_NAME)

        r1 = tb.add_node_from_template(
            client, project_id, c3745_template_id, x=-200, y=-100, rename="R1"
        )
        r2 = tb.add_node_from_template(
            client, project_id, c3745_template_id, x=200, y=-100, rename="R2"
        )

        sw1 = tb.add_raw_node(
            client,
            project_id,
            name="SW1",
            node_type="ethernet_switch",
            x=-200,
            y=100,
            symbol=":/symbols/ethernet_switch.svg",
        )
        sw2 = tb.add_raw_node(
            client,
            project_id,
            name="SW2",
            node_type="ethernet_switch",
            x=200,
            y=100,
            symbol=":/symbols/ethernet_switch.svg",
        )

        tb.configure_switch_vlans(client, project_id, sw1)
        tb.configure_switch_vlans(client, project_id, sw2)

        pc1 = tb.add_vpcs_node(client, project_id, name="PC1", x=-300, y=300)
        pc2 = tb.add_vpcs_node(client, project_id, name="PC2", x=-100, y=300)
        pc3 = tb.add_vpcs_node(client, project_id, name="PC3", x=100, y=300)
        pc4 = tb.add_vpcs_node(client, project_id, name="PC4", x=300, y=300)

        # Router back-to-back link on f0/1.
        tb.link(client, project_id, r1, ROUTER_F01_PORT, r2, ROUTER_F01_PORT)

        # Router-to-switch trunk on f0/0 <-> Eth2.
        tb.link(client, project_id, r1, ROUTER_F00_PORT, sw1, 2)
        tb.link(client, project_id, r2, ROUTER_F00_PORT, sw2, 2)

        # PCs on access ports.
        tb.link(client, project_id, sw1, 0, pc1, 0)
        tb.link(client, project_id, sw1, 1, pc2, 0)
        tb.link(client, project_id, sw2, 0, pc3, 0)
        tb.link(client, project_id, sw2, 1, pc4, 0)

        return project_id
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the ospf-vlan lab template in GNS3.")
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

    print(f"TEMPLATE_PROJECT_ID={project_id}")


if __name__ == "__main__":
    main()
