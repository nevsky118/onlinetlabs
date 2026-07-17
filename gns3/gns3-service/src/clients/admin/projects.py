# GNS3 project management: create, duplicate, open, delete, list.

import asyncio

import httpx

from ._http import _retry_on_401, _transient_retry


class ProjectsMixin:
    @_transient_retry
    @_retry_on_401
    async def create_project(self, name: str) -> dict:
        response = await self._client.post(
            "/v3/projects",
            json={"name": name},
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response.json()

    @_retry_on_401
    async def list_projects(self) -> list[dict]:
        response = await self._client.get("/v3/projects", headers=self._auth_headers())
        response.raise_for_status()
        return response.json()

    @_transient_retry
    @_retry_on_401
    async def duplicate_project(self, project_id: str, name: str | None = None) -> dict:
        body = {"name": name} if name else {}
        # GNS3 responds 409 while the source project is still opening/locked.
        # We back off so launch and reset aren't racy.
        last_response: httpx.Response | None = None
        for attempt in range(5):
            last_response = await self._client.post(
                f"/v3/projects/{project_id}/duplicate",
                json=body,
                headers=self._auth_headers(),
            )
            if last_response.status_code != 409:
                break
            await asyncio.sleep(0.5 * (attempt + 1))
        last_response.raise_for_status()
        return last_response.json()

    @_transient_retry
    @_retry_on_401
    async def open_project(self, project_id: str) -> dict:
        response = await self._client.post(
            f"/v3/projects/{project_id}/open",
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response.json()

    @_retry_on_401
    async def delete_project(self, project_id: str) -> None:
        response = await self._client.delete(
            f"/v3/projects/{project_id}",
            headers=self._auth_headers(),
        )
        response.raise_for_status()
