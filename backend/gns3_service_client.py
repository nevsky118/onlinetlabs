"""Async HTTP client for gns3-service (provision/reset/teardown)."""

import httpx


class Gns3ServiceClient:
    """Async HTTP client for gns3-service, used to manage student sessions."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 60.0,
        internal_token: str | None = None,
    ):
        """Configures the httpx client with a bearer token and transport retries."""
        # Bearer token for /v1/exec/vtysh. Without it gns3-service rejects the request.
        headers: dict[str, str] = {}
        if internal_token:
            headers["Authorization"] = f"Bearer {internal_token}"
        # Transport retries at the connection level. httpx itself re-establishes
        # the network connection on ConnectError/ReadError up to three times.
        # 5xx HTTP responses are not covered here, they need a retry in code.
        transport = httpx.AsyncHTTPTransport(retries=3)
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers=headers,
            transport=transport,
        )

    async def create_session(self, user_id: str, template_project_id: str) -> dict:
        """Creates a new session for the user from the template project."""
        resp = await self._client.post(
            "/sessions",
            json={"user_id": user_id, "lab_template_project_id": template_project_id},
        )
        resp.raise_for_status()
        return resp.json()

    async def reset_project(self, gns3_service_session_id: str, template_project_id: str) -> dict:
        """Resets the session project back to the template's initial state."""
        resp = await self._client.post(
            f"/sessions/{gns3_service_session_id}/reset-project",
            json={"lab_template_project_id": template_project_id},
        )
        resp.raise_for_status()
        return resp.json()

    async def delete_session(self, gns3_service_session_id: str) -> None:
        """Deletes the session and frees its resources."""
        resp = await self._client.delete(f"/sessions/{gns3_service_session_id}")
        resp.raise_for_status()

    async def get_state(self, session_id: str) -> dict:
        """Gets the current state of the session and its nodes."""
        resp = await self._client.get(f"/sessions/{session_id}/state")
        resp.raise_for_status()
        return resp.json()

    async def node_action(self, session_id: str, node_id: str, action: str) -> None:
        """Performs an action on a single node (start, stop, etc.)."""
        resp = await self._client.post(f"/sessions/{session_id}/nodes/{node_id}/{action}")
        resp.raise_for_status()

    async def bulk_node_action(self, session_id: str, action: str) -> None:
        """Performs an action on all session nodes at once."""
        # Per-call timeout 180s: with backend-side semaphore (8 concurrent)
        # and ~10s per bulk-start on gns3-server, 50-student queue takes ~60s.
        # 180s gives 3x headroom for cold caches / heavier topologies.
        resp = await self._client.post(
            f"/sessions/{session_id}/nodes/{action}",
            timeout=180.0,
        )
        resp.raise_for_status()

    async def get_activity(
        self,
        session_id: str,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict:
        """Gets the session activity feed with cursor-based pagination."""
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        resp = await self._client.get(f"/sessions/{session_id}/activity", params=params)
        resp.raise_for_status()
        return resp.json()

    async def exec_vtysh(self, project_id: str, node_id: str, command: str) -> dict:
        """Runs a vtysh command on a docker node via the gns3-service exec endpoint.

        Returns: `{stdout, stderr, exit_code}`.
        """
        resp = await self._client.post(
            "/v1/exec/vtysh",
            json={"project_id": project_id, "node_id": node_id, "command": command},
        )
        resp.raise_for_status()
        return resp.json()

    async def build_template(self, lab_slug: str) -> str:
        """Builds the GNS3 template for the lab in gns3-service. Returns template_project_id."""
        resp = await self._client.post(f"/v1/templates/{lab_slug}/build", timeout=600.0)
        resp.raise_for_status()
        return resp.json()["template_project_id"]

    async def close(self) -> None:
        """Closes the HTTP client and its connections."""
        await self._client.aclose()
