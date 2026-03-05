# Маппинг GNS3 JSON → SDK models.

from collections import Counter

from onlinetlabs_mcp_sdk.models import Component, ComponentDetail, SystemOverview


def node_to_component(node: dict) -> Component:
    return Component(
        id=node["node_id"],
        name=node["name"],
        type=node["node_type"],
        status=node["status"],
        summary=f"{node['node_type']} {node['name']} ({node['status']})",
    )


def node_to_component_detail(node: dict, peer_node_ids: list[str] | None = None) -> ComponentDetail:
    return ComponentDetail(
        id=node["node_id"],
        name=node["name"],
        type=node["node_type"],
        status=node["status"],
        summary=f"{node['node_type']} {node['name']} ({node['status']})",
        properties={
            "console": node.get("console"),
            "console_type": node.get("console_type"),
            "console_host": node.get("console_host"),
            "ports": node.get("ports", []),
            "compute_id": node.get("compute_id"),
        },
        configuration=None,
        relationships=peer_node_ids or [],
    )


def link_to_component(link: dict, node_names: dict[str, str]) -> Component:
    """node_names: {node_id: name} для человекочитаемого имени."""
    nodes = link["nodes"]
    if len(nodes) >= 2:
        a_name = node_names.get(nodes[0]["node_id"], nodes[0]["node_id"])
        b_name = node_names.get(nodes[1]["node_id"], nodes[1]["node_id"])
        a_port = f"{nodes[0]['adapter_number']}/{nodes[0]['port_number']}"
        b_port = f"{nodes[1]['adapter_number']}/{nodes[1]['port_number']}"
        name = f"{a_name}:{a_port} <-> {b_name}:{b_port}"
        summary = f"Link between {a_name} and {b_name}"
    else:
        name = f"link-{link['link_id']}"
        summary = "Partial link"

    status = "capturing" if link.get("capturing") else "active"

    return Component(id=link["link_id"], name=name, type="link", status=status, summary=summary)


def link_to_component_detail(link: dict, node_names: dict[str, str]) -> ComponentDetail:
    base = link_to_component(link, node_names)
    return ComponentDetail(
        **base.model_dump(),
        properties={
            "nodes": link["nodes"],
            "filters": link.get("filters", {}),
            "link_type": link.get("link_type"),
            "capturing": link.get("capturing", False),
        },
        relationships=[node["node_id"] for node in link["nodes"]],
    )


def build_system_overview(
    nodes: list[dict], links: list[dict], version: dict, project_name: str,
) -> SystemOverview:
    type_counts = Counter(node["node_type"] for node in nodes)
    type_counts["link"] = len(links)

    status_counts = Counter(node["status"] for node in nodes)
    for link in links:
        status = "capturing" if link.get("capturing") else "active"
        status_counts[status] += 1

    return SystemOverview(
        system_name="GNS3",
        system_version=version.get("version"),
        component_count=len(nodes) + len(links),
        components_by_type=dict(type_counts),
        components_by_status=dict(status_counts),
        summary=f"Project '{project_name}': {len(nodes)} nodes, {len(links)} links",
    )
