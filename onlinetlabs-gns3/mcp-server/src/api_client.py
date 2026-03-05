# Thin httpx wrapper for GNS3 REST API v3.

import httpx

from onlinetlabs_mcp_sdk.errors import (
    TargetSystemAPIError,
    TargetSystemConnectionError,
)


class GNS3ApiClient:
    """Thin httpx client, one method per GNS3 endpoint."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def _request(self, method: str, path: str, **kwargs) -> dict | list | None:
        """Common request handler with error mapping."""
        try:
            response = await self.client.request(method, path, **kwargs)
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise TargetSystemConnectionError(str(e)) from e

        if response.status_code >= 400:
            body = response.text
            raise TargetSystemAPIError(
                status_code=response.status_code,
                response_body=body,
            )
        if response.status_code == 204:
            return None
        return response.json()

    # -- Server --
    async def get_version(self) -> dict:
        return await self._request("GET", "/v3/version")

    # -- Projects --
    async def list_projects(self) -> list[dict]:
        return await self._request("GET", "/v3/projects")

    async def get_project(self, project_id: str) -> dict:
        return await self._request("GET", f"/v3/projects/{project_id}")

    async def open_project(self, project_id: str) -> dict:
        return await self._request("POST", f"/v3/projects/{project_id}/open")

    async def close_project(self, project_id: str) -> dict:
        return await self._request("POST", f"/v3/projects/{project_id}/close")

    async def lock_project(self, project_id: str) -> dict:
        return await self._request("POST", f"/v3/projects/{project_id}/lock")

    async def unlock_project(self, project_id: str) -> dict:
        return await self._request("POST", f"/v3/projects/{project_id}/unlock")

    async def duplicate_project(self, project_id: str) -> dict:
        return await self._request("POST", f"/v3/projects/{project_id}/duplicate")

    # -- Nodes --
    async def list_nodes(self, project_id: str) -> list[dict]:
        return await self._request("GET", f"/v3/projects/{project_id}/nodes")

    async def get_node(self, project_id: str, node_id: str) -> dict:
        return await self._request(
            "GET", f"/v3/projects/{project_id}/nodes/{node_id}"
        )

    async def start_node(self, project_id: str, node_id: str) -> dict:
        return await self._request(
            "POST", f"/v3/projects/{project_id}/nodes/{node_id}/start"
        )

    async def stop_node(self, project_id: str, node_id: str) -> dict:
        return await self._request(
            "POST", f"/v3/projects/{project_id}/nodes/{node_id}/stop"
        )

    async def reload_node(self, project_id: str, node_id: str) -> dict:
        return await self._request(
            "POST", f"/v3/projects/{project_id}/nodes/{node_id}/reload"
        )

    async def suspend_node(self, project_id: str, node_id: str) -> dict:
        return await self._request(
            "POST", f"/v3/projects/{project_id}/nodes/{node_id}/suspend"
        )

    async def isolate_node(self, project_id: str, node_id: str) -> dict:
        return await self._request(
            "POST", f"/v3/projects/{project_id}/nodes/{node_id}/isolate"
        )

    async def unisolate_node(self, project_id: str, node_id: str) -> dict:
        return await self._request(
            "POST", f"/v3/projects/{project_id}/nodes/{node_id}/unisolate"
        )

    async def start_all_nodes(self, project_id: str) -> None:
        await self._request("POST", f"/v3/projects/{project_id}/nodes/start")

    async def stop_all_nodes(self, project_id: str) -> None:
        await self._request("POST", f"/v3/projects/{project_id}/nodes/stop")

    async def create_node_from_template(
        self, project_id: str, template_id: str, x: int = 0, y: int = 0
    ) -> dict:
        return await self._request(
            "POST",
            f"/v3/projects/{project_id}/templates/{template_id}",
            json={"x": x, "y": y},
        )

    async def reset_console(self, project_id: str, node_id: str) -> None:
        await self._request(
            "POST", f"/v3/projects/{project_id}/nodes/{node_id}/console/reset"
        )

    # -- Links --
    async def list_links(self, project_id: str) -> list[dict]:
        return await self._request("GET", f"/v3/projects/{project_id}/links")

    async def create_link(self, project_id: str, nodes: list[dict]) -> dict:
        return await self._request(
            "POST", f"/v3/projects/{project_id}/links", json={"nodes": nodes}
        )

    async def delete_link(self, project_id: str, link_id: str) -> None:
        await self._request(
            "DELETE", f"/v3/projects/{project_id}/links/{link_id}"
        )

    async def start_capture(self, project_id: str, link_id: str) -> dict:
        return await self._request(
            "POST",
            f"/v3/projects/{project_id}/links/{link_id}/capture/start",
        )

    async def stop_capture(self, project_id: str, link_id: str) -> dict:
        return await self._request(
            "POST",
            f"/v3/projects/{project_id}/links/{link_id}/capture/stop",
        )

    async def set_link_filter(
        self, project_id: str, link_id: str, filters: dict
    ) -> dict:
        return await self._request(
            "PUT",
            f"/v3/projects/{project_id}/links/{link_id}",
            json={"filters": filters},
        )

    # -- Templates --
    async def list_templates(self) -> list[dict]:
        return await self._request("GET", "/v3/templates")

    # -- Snapshots --
    async def list_snapshots(self, project_id: str) -> list[dict]:
        return await self._request(
            "GET", f"/v3/projects/{project_id}/snapshots"
        )

    async def create_snapshot(self, project_id: str, name: str) -> dict:
        return await self._request(
            "POST",
            f"/v3/projects/{project_id}/snapshots",
            json={"name": name},
        )

    async def restore_snapshot(
        self, project_id: str, snapshot_id: str
    ) -> dict:
        return await self._request(
            "POST",
            f"/v3/projects/{project_id}/snapshots/{snapshot_id}/restore",
        )
