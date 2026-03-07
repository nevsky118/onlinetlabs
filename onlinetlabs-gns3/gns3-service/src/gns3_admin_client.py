# Httpx клиент для GNS3 v3 admin API.

import httpx


class GNS3AdminClient:
    """Минимальный клиент для управления users/ACL."""

    def __init__(self, base_url: str, admin_user: str, admin_password: str) -> None:
        self._base_url = base_url
        self._admin_user = admin_user
        self._admin_password = admin_password
        self._client = httpx.AsyncClient(base_url=base_url, timeout=30)
        self.token: str | None = None

    async def authenticate(self) -> None:
        """Получить admin JWT."""
        response = await self._client.post(
            "/v3/access/users/authenticate",
            json={"username": self._admin_user, "password": self._admin_password},
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        self._client.headers["Authorization"] = f"Bearer {self.token}"
        self._admin_password = ""

    async def create_user(self, username: str, password: str) -> dict:
        response = await self._client.post("/v3/access/users", json={"username": username, "password": password})
        response.raise_for_status()
        return response.json()

    async def update_user_password(self, user_id: str, new_password: str) -> None:
        response = await self._client.put(f"/v3/access/users/{user_id}", json={"password": new_password})
        response.raise_for_status()

    async def delete_user(self, user_id: str) -> None:
        response = await self._client.delete(f"/v3/access/users/{user_id}")
        response.raise_for_status()

    async def get_user_token(self, username: str, password: str) -> str:
        response = await self._client.post("/v3/access/users/authenticate", json={"username": username, "password": password})
        response.raise_for_status()
        return response.json()["access_token"]

    async def duplicate_project(self, project_id: str, name: str | None = None) -> dict:
        body = {"name": name} if name else {}
        response = await self._client.post(f"/v3/projects/{project_id}/duplicate", json=body)
        response.raise_for_status()
        return response.json()

    async def create_role(self, name: str) -> dict:
        response = await self._client.post("/v3/access/roles", json={"name": name})
        response.raise_for_status()
        return response.json()

    async def create_acl(self, path: str, role_id: str, user_id: str, allowed: bool = True) -> dict:
        response = await self._client.post("/v3/access/acl", json={
            "path": path, "role_id": role_id, "user_id": user_id,
            "ace_type": "user", "allowed": allowed,
        })
        response.raise_for_status()
        return response.json()

    async def assign_role_to_user(self, user_id: str, role_id: str) -> None:
        response = await self._client.put(f"/v3/access/users/{user_id}", json={"role_id": role_id})
        response.raise_for_status()

    async def open_project(self, project_id: str) -> dict:
        response = await self._client.post(f"/v3/projects/{project_id}/open")
        response.raise_for_status()
        return response.json()

    async def delete_project(self, project_id: str) -> None:
        response = await self._client.delete(f"/v3/projects/{project_id}")
        response.raise_for_status()

    async def delete_role(self, role_id: str) -> None:
        response = await self._client.delete(f"/v3/access/roles/{role_id}")
        response.raise_for_status()

    async def get_builtin_role(self, name: str = "User") -> dict:
        """Найти встроенную роль по имени (User, Administrator, Auditor и т.д.)."""
        response = await self._client.get("/v3/access/roles")
        response.raise_for_status()
        for role in response.json():
            if role["is_builtin"] and role["name"] == name:
                return role
        raise ValueError(f"Built-in role '{name}' not found")

    async def close(self) -> None:
        await self._client.aclose()
