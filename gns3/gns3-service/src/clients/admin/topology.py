# Работа с топологией проекта GNS3: узлы, линки, действия над узлами.

from ._http import _retry_on_401


class TopologyMixin:
    _VALID_NODE_ACTIONS = {"start", "stop", "suspend", "reload"}

    @_retry_on_401
    async def get_nodes(self, project_id: str) -> list[dict]:
        response = await self._client.get(
            f"/v3/projects/{project_id}/nodes",
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response.json()

    @_retry_on_401
    async def get_links(self, project_id: str) -> list[dict]:
        response = await self._client.get(
            f"/v3/projects/{project_id}/links",
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response.json()

    @_retry_on_401
    async def node_action(self, project_id: str, node_id: str, action: str) -> None:
        if action not in self._VALID_NODE_ACTIONS:
            raise ValueError(f"Invalid action: {action}")
        response = await self._client.post(
            f"/v3/projects/{project_id}/nodes/{node_id}/{action}",
            headers=self._auth_headers(),
            # GNS3 v3 требует JSON-тело у node-action POST'ов, иначе 422.
            json={},
        )
        response.raise_for_status()

    @_retry_on_401
    async def bulk_node_action(self, project_id: str, action: str) -> None:
        if action not in self._VALID_NODE_ACTIONS:
            raise ValueError(f"Invalid action: {action}")
        response = await self._client.post(
            f"/v3/projects/{project_id}/nodes/{action}",
            headers=self._auth_headers(),
            json={},
        )
        response.raise_for_status()
