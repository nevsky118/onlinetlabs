#!/usr/bin/env python3
"""Build the CCNA-canonical ospf-vlan lab template project in GNS3 v3 (IOSv + IOSvL2).

Topology mirrors the lite/builtin variant but uses real Cisco images:

    PC1 - e0 - Gi0/0 SW1 Gi0/2 - Gi0/0 R1 Gi0/1 - Gi0/1 R2 Gi0/0 - Gi0/2 SW2 Gi0/0 - e0 PC3
    PC2 - e0 - Gi0/1 SW1                                                 SW2 Gi0/1 - e0 PC4

R1, R2:  Cisco IOSv (template name "Cisco IOSv")
SW1, SW2: Cisco IOSvL2 (template name "Cisco IOSvL2")
PC1..PC4: builtin VPCS

Port (adapter, port) numbering for IOSvL2 is NOT hardcoded: GNS3 reports it via
properties.port_segment_size which can differ from the dynamips c3745 model.
Instead each Cisco node is GET'd after creation and its ports[] array is scanned
by `name` ("GigabitEthernetX/Y") to discover the actual (adapter_number,
port_number) pair to feed into the link request.

CLI:
    python build_iosvl2_lab_template.py            # idempotent
    python build_iosvl2_lab_template.py --force    # delete existing and rebuild

On success prints exactly one line to stdout:
    IOSVL2_TEMPLATE_PROJECT_ID=<uuid>

Exit codes:
    0  success or existing project found (no --force)
    2  preflight failed: required Cisco templates missing, or GNS3 API error
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

PROJECT_NAME = "ospf-vlan-template-iosvl2"

ROUTER_TEMPLATE_NAME = "Cisco IOSv"
SWITCH_TEMPLATE_NAME = "Cisco IOSvL2"

PREFLIGHT_ERROR_MESSAGE = (
    "Cisco IOSv or IOSvL2 template not registered. "
    "Place qcow2 images in gns3/images/QEMU/ and restart gns3-service. "
    "See docs/deployment/x86-production.md."
)


def _preflight(client: httpx.Client) -> tuple[str, str]:
    """Return (iosv_template_id, iosvl2_template_id) or raise SystemExit(2)."""
    templates = tb.list_templates(client)
    iosv_id = tb.find_template_id(templates, ROUTER_TEMPLATE_NAME)
    iosvl2_id = tb.find_template_id(templates, SWITCH_TEMPLATE_NAME)
    if iosv_id is None or iosvl2_id is None:
        sys.stderr.write(PREFLIGHT_ERROR_MESSAGE + "\n")
        raise SystemExit(2)
    return iosv_id, iosvl2_id


def build_template(force: bool) -> str:
    client = httpx.Client(base_url=GNS3_URL, timeout=120)
    try:
        tb.authenticate(client, GNS3_USER, GNS3_PASSWORD)

        iosv_template_id, iosvl2_template_id = _preflight(client)

        existing = tb.find_project_by_name(client, PROJECT_NAME)
        if existing and not force:
            return existing["project_id"]
        if existing and force:
            tb.delete_project(client, existing["project_id"])

        project_id = tb.create_project(client, PROJECT_NAME)

        r1 = tb.add_node_from_template(client, project_id, iosv_template_id, x=-200, y=-100, rename="R1")
        r2 = tb.add_node_from_template(client, project_id, iosv_template_id, x=200, y=-100, rename="R2")

        sw1 = tb.add_node_from_template(client, project_id, iosvl2_template_id, x=-200, y=100, rename="SW1")
        sw2 = tb.add_node_from_template(client, project_id, iosvl2_template_id, x=200, y=100, rename="SW2")

        pc1 = tb.add_vpcs_node(client, project_id, name="PC1", x=-300, y=300)
        pc2 = tb.add_vpcs_node(client, project_id, name="PC2", x=-100, y=300)
        pc3 = tb.add_vpcs_node(client, project_id, name="PC3", x=100, y=300)
        pc4 = tb.add_vpcs_node(client, project_id, name="PC4", x=300, y=300)

        # Резолвим (adapter, port) tuples динамически: у IOSvL2 свой port_segment_size.
        r1_gi00 = tb.resolve_port(client, project_id, r1, "GigabitEthernet0/0")
        r1_gi01 = tb.resolve_port(client, project_id, r1, "GigabitEthernet0/1")
        r2_gi00 = tb.resolve_port(client, project_id, r2, "GigabitEthernet0/0")
        r2_gi01 = tb.resolve_port(client, project_id, r2, "GigabitEthernet0/1")

        sw1_gi00 = tb.resolve_port(client, project_id, sw1, "GigabitEthernet0/0")
        sw1_gi01 = tb.resolve_port(client, project_id, sw1, "GigabitEthernet0/1")
        sw1_gi02 = tb.resolve_port(client, project_id, sw1, "GigabitEthernet0/2")
        sw2_gi00 = tb.resolve_port(client, project_id, sw2, "GigabitEthernet0/0")
        sw2_gi01 = tb.resolve_port(client, project_id, sw2, "GigabitEthernet0/1")
        sw2_gi02 = tb.resolve_port(client, project_id, sw2, "GigabitEthernet0/2")

        pc1_e0 = tb.resolve_port(client, project_id, pc1, "Ethernet0")
        pc2_e0 = tb.resolve_port(client, project_id, pc2, "Ethernet0")
        pc3_e0 = tb.resolve_port(client, project_id, pc3, "Ethernet0")
        pc4_e0 = tb.resolve_port(client, project_id, pc4, "Ethernet0")

        # Backbone: R1.Gi0/1 <-> R2.Gi0/1.
        tb.link(client, project_id, r1, r1_gi01[1], r2, r2_gi01[1],
                a_adapter=r1_gi01[0], b_adapter=r2_gi01[0])

        # Router-to-switch trunks: R1.Gi0/0 <-> SW1.Gi0/2, R2.Gi0/0 <-> SW2.Gi0/2.
        tb.link(client, project_id, r1, r1_gi00[1], sw1, sw1_gi02[1],
                a_adapter=r1_gi00[0], b_adapter=sw1_gi02[0])
        tb.link(client, project_id, r2, r2_gi00[1], sw2, sw2_gi02[1],
                a_adapter=r2_gi00[0], b_adapter=sw2_gi02[0])

        # PC access ports.
        tb.link(client, project_id, sw1, sw1_gi00[1], pc1, pc1_e0[1],
                a_adapter=sw1_gi00[0], b_adapter=pc1_e0[0])
        tb.link(client, project_id, sw1, sw1_gi01[1], pc2, pc2_e0[1],
                a_adapter=sw1_gi01[0], b_adapter=pc2_e0[0])
        tb.link(client, project_id, sw2, sw2_gi00[1], pc3, pc3_e0[1],
                a_adapter=sw2_gi00[0], b_adapter=pc3_e0[0])
        tb.link(client, project_id, sw2, sw2_gi01[1], pc4, pc4_e0[1],
                a_adapter=sw2_gi01[0], b_adapter=pc4_e0[0])

        return project_id
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the ospf-vlan IOSv/IOSvL2 lab template in GNS3."
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

    print(f"IOSVL2_TEMPLATE_PROJECT_ID={project_id}")


if __name__ == "__main__":
    main()
