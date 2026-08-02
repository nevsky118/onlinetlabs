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
