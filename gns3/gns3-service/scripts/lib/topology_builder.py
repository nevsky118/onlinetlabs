# Shared GNS3 operations for build_*_lab_template.py.
#
# Authentication, template/project lookup, node creation and link creation live
# here. Every build script assembles its own topology on top of these
# primitives without duplicating the HTTP calls.

from __future__ import annotations

import httpx


def authenticate(client: httpx.Client, username: str, password: str) -> None:
    """Authenticate against GNS3 and set the Bearer token on the client."""
    response = client.post(
        "/v3/access/users/authenticate",
        json={"username": username, "password": password},
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"


def list_templates(client: httpx.Client) -> list[dict]:
    response = client.get("/v3/templates")
    response.raise_for_status()
    return response.json()


def find_template_id(templates: list[dict], name: str) -> str | None:
    for template in templates:
        if template.get("name") == name:
            return template["template_id"]
    return None


def find_project_by_name(client: httpx.Client, name: str) -> dict | None:
    response = client.get("/v3/projects")
    response.raise_for_status()
    for project in response.json():
        if project.get("name") == name:
            return project
    return None


def delete_project(client: httpx.Client, project_id: str) -> None:
    response = client.delete(f"/v3/projects/{project_id}")
    response.raise_for_status()


def create_project(client: httpx.Client, name: str) -> str:
    response = client.post("/v3/projects", json={"name": name})
    response.raise_for_status()
    return response.json()["project_id"]


def add_node_from_template(
    client: httpx.Client,
    project_id: str,
    template_id: str,
    *,
    x: int,
    y: int,
    rename: str | None = None,
) -> str:
    """Deploy a node from a template at coordinates x/y, optionally renaming it."""
    response = client.post(
        f"/v3/projects/{project_id}/templates/{template_id}",
        json={"x": x, "y": y},
    )
    response.raise_for_status()
    node = response.json()
    node_id = node["node_id"]

    if rename and node.get("name") != rename:
        rename_response = client.put(
            f"/v3/projects/{project_id}/nodes/{node_id}",
            json={"name": rename},
        )
        rename_response.raise_for_status()
    return node_id


def add_raw_node(
    client: httpx.Client,
    project_id: str,
    *,
    name: str,
    node_type: str,
    x: int,
    y: int,
    symbol: str,
) -> str:
    """Create a node without a template (ethernet_switch, vpcs, and so on)."""
    response = client.post(
        f"/v3/projects/{project_id}/nodes",
        json={
            "name": name,
            "node_type": node_type,
            "compute_id": "local",
            "x": x,
            "y": y,
            "symbol": symbol,
        },
    )
    response.raise_for_status()
    return response.json()["node_id"]


def add_vpcs_node(
    client: httpx.Client,
    project_id: str,
    *,
    name: str,
    x: int,
    y: int,
) -> str:
    """Wrapper for VPCS with the default GNS3 symbol (affinity blue client), same as native VPCS."""
    return add_raw_node(
        client,
        project_id,
        name=name,
        node_type="vpcs",
        x=x,
        y=y,
        symbol=":/symbols/affinity/square/blue/client.svg",
    )


def get_node(client: httpx.Client, project_id: str, node_id: str) -> dict:
    response = client.get(f"/v3/projects/{project_id}/nodes/{node_id}")
    response.raise_for_status()
    return response.json()


def resolve_port(
    client: httpx.Client,
    project_id: str,
    node_id: str,
    port_name: str,
) -> tuple[int, int]:
    """Find (adapter_number, port_number) by the port name from ports[]."""
    node = get_node(client, project_id, node_id)
    for port in node.get("ports", []):
        if port.get("name") == port_name:
            return port["adapter_number"], port["port_number"]
    available = ", ".join(p.get("name", "?") for p in node.get("ports", []))
    raise SystemExit(
        f"Port {port_name!r} not found on node {node.get('name')!r} "
        f"({node_id}). Available ports: {available}"
    )


def link(
    client: httpx.Client,
    project_id: str,
    a_node: str,
    a_port: int,
    b_node: str,
    b_port: int,
    *,
    a_adapter: int = 0,
    b_adapter: int = 0,
) -> None:
    """Connect two nodes on the given adapter/port."""
    response = client.post(
        f"/v3/projects/{project_id}/links",
        json={
            "nodes": [
                {"node_id": a_node, "adapter_number": a_adapter, "port_number": a_port},
                {"node_id": b_node, "adapter_number": b_adapter, "port_number": b_port},
            ],
        },
    )
    response.raise_for_status()


def configure_switch_vlans(
    client: httpx.Client,
    project_id: str,
    node_id: str,
    *,
    access_ports: dict[int, int] | None = None,
    trunk_ports: tuple[int, ...] = (),
) -> None:
    """Configure an ethernet_switch, access ports and dot1q trunks.

    access_ports: mapping of port_number -> vlan_id for access ports.
    trunk_ports: list of port_number values to switch over to a dot1q trunk.
    Defaults match our OSPF+VLAN target, Eth0->vlan10, Eth1->vlan20, Eth2 trunk.
    """
    if access_ports is None:
        access_ports = {0: 10, 1: 20}
    if not trunk_ports:
        trunk_ports = (2,)

    get_response = client.get(f"/v3/projects/{project_id}/nodes/{node_id}")
    get_response.raise_for_status()
    ports_mapping = list(get_response.json()["properties"]["ports_mapping"])

    for port in ports_mapping:
        port_number = port["port_number"]
        if port_number in access_ports:
            port["type"] = "access"
            port["vlan"] = access_ports[port_number]
            port["ethertype"] = "0x8100"
        elif port_number in trunk_ports:
            port["type"] = "dot1q"
            port["vlan"] = 1
            port["ethertype"] = "0x8100"

    put_response = client.put(
        f"/v3/projects/{project_id}/nodes/{node_id}",
        json={"properties": {"ports_mapping": ports_mapping}},
    )
    put_response.raise_for_status()

    verify_response = client.get(f"/v3/projects/{project_id}/nodes/{node_id}")
    verify_response.raise_for_status()
    ports_after = verify_response.json()["properties"]["ports_mapping"]
    by_port = {p["port_number"]: p for p in ports_after}
    for port_number, vlan in access_ports.items():
        port_after = by_port[port_number]
        if port_after["vlan"] != vlan or port_after["type"] != "access":
            raise SystemExit(
                f"Switch {node_id} port {port_number} access vlan {vlan} not persisted: {port_after}"
            )
    for port_number in trunk_ports:
        if by_port[port_number]["type"] != "dot1q":
            raise SystemExit(
                f"Switch {node_id} port {port_number} trunk not persisted: {by_port[port_number]}"
            )


def set_console_type(
    client: httpx.Client,
    project_id: str,
    node_id: str,
    console_type: str,
) -> None:
    """Set the console_type of a node (for example none for docker nodes).

    FRR docker nodes get none so that GNS3 does not try to attach a telnet
    console over WS to the Docker API, which fails on Docker Desktop macOS
    (handshake 400) and breaks the node start. The routers are auto-configured,
    they do not need a console.
    """
    response = client.put(
        f"/v3/projects/{project_id}/nodes/{node_id}",
        json={"console_type": console_type},
    )
    response.raise_for_status()


def append_docker_env(
    client: httpx.Client,
    project_id: str,
    node_id: str,
    extra_env: str,
) -> None:
    """Append env variables to properties.environment of a docker node.

    GNS3 stores env as a newline-separated string. We keep the FRR_* values the
    template already set and append role-specific ones (for example FRR_ROLE=R1).
    """
    get_response = client.get(f"/v3/projects/{project_id}/nodes/{node_id}")
    get_response.raise_for_status()
    existing = get_response.json()["properties"].get("environment") or ""
    merged = (existing.rstrip("\n") + "\n" + extra_env).lstrip("\n")
    put_response = client.put(
        f"/v3/projects/{project_id}/nodes/{node_id}",
        json={"properties": {"environment": merged}},
    )
    put_response.raise_for_status()

    verify_response = client.get(f"/v3/projects/{project_id}/nodes/{node_id}")
    verify_response.raise_for_status()
    after = verify_response.json()["properties"].get("environment") or ""
    if extra_env not in after.split("\n"):
        raise SystemExit(
            f"Node {node_id} env not persisted; expected line {extra_env!r} in {after!r}"
        )
