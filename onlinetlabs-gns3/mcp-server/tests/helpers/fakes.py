# Fake implementations для тестов.

from onlinetlabs_mcp_sdk.errors import TargetSystemAPIError

from tests.helpers.factories import (
    build_gns3_link,
    build_gns3_node,
    build_gns3_project,
    build_gns3_version,
)


class FakeGNS3ApiClient:
    """Мок GNS3ApiClient для тестов без HTTP."""

    def __init__(self):
        self.nodes = [
            build_gns3_node(node_id="n1", name="R1", node_type="vpcs", status="started"),
            build_gns3_node(node_id="n2", name="R2", node_type="qemu", status="stopped"),
        ]
        self.links = [
            build_gns3_link(
                link_id="l1",
                nodes=[
                    {"node_id": "n1", "adapter_number": 0, "port_number": 0},
                    {"node_id": "n2", "adapter_number": 0, "port_number": 0},
                ],
            ),
        ]

    async def get_version(self) -> dict:
        return build_gns3_version()

    async def list_projects(self) -> list[dict]:
        return [build_gns3_project()]

    async def get_project(self, project_id: str) -> dict:
        return build_gns3_project(project_id=project_id)

    async def list_nodes(self, project_id: str) -> list[dict]:
        return self.nodes

    async def get_node(self, project_id: str, node_id: str) -> dict:
        for node in self.nodes:
            if node["node_id"] == node_id:
                return node
        raise TargetSystemAPIError(status_code=404, response_body="Node not found")

    async def list_links(self, project_id: str) -> list[dict]:
        return self.links

    async def start_node(self, project_id: str, node_id: str) -> dict:
        return {}

    async def stop_node(self, project_id: str, node_id: str) -> dict:
        return {}

    async def reload_node(self, project_id: str, node_id: str) -> dict:
        return {}

    async def suspend_node(self, project_id: str, node_id: str) -> dict:
        return {}

    async def isolate_node(self, project_id: str, node_id: str) -> dict:
        return {}

    async def unisolate_node(self, project_id: str, node_id: str) -> dict:
        return {}

    async def start_all_nodes(self, project_id: str) -> None:
        pass

    async def stop_all_nodes(self, project_id: str) -> None:
        pass

    async def create_link(self, project_id: str, nodes: list[dict]) -> dict:
        return build_gns3_link()

    async def delete_link(self, project_id: str, link_id: str) -> None:
        pass

    async def start_capture(self, project_id: str, link_id: str) -> dict:
        return {}

    async def stop_capture(self, project_id: str, link_id: str) -> dict:
        return {}

    async def set_link_filter(self, project_id: str, link_id: str, filters: dict) -> dict:
        return {}

    async def list_templates(self) -> list[dict]:
        return [{"template_id": "t1", "name": "VPCS", "template_type": "vpcs"}]

    async def create_node_from_template(self, project_id: str, template_id: str, x: int = 0, y: int = 0) -> dict:
        return build_gns3_node()

    async def list_snapshots(self, project_id: str) -> list[dict]:
        return [{"snapshot_id": "s1", "name": "checkpoint1"}]

    async def create_snapshot(self, project_id: str, name: str) -> dict:
        return {"snapshot_id": "s1", "name": name}

    async def restore_snapshot(self, project_id: str, snapshot_id: str) -> dict:
        return {}

    async def open_project(self, project_id: str) -> dict:
        return build_gns3_project(project_id=project_id)

    async def close_project(self, project_id: str) -> dict:
        return build_gns3_project(project_id=project_id, status="closed")

    async def lock_project(self, project_id: str) -> dict:
        return {}

    async def unlock_project(self, project_id: str) -> dict:
        return {}

    async def duplicate_project(self, project_id: str) -> dict:
        return build_gns3_project()

    async def reset_console(self, project_id: str, node_id: str) -> None:
        pass
