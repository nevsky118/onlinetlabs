# Управление ролями GNS3: создание, удаление, присвоение пользователю, кеш встроенных.

from ._http import _retry_on_401


class RolesMixin:
    @_retry_on_401
    async def create_role(self, name: str) -> dict:
        response = await self._client.post(
            "/v3/access/roles",
            json={"name": name},
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response.json()

    @_retry_on_401
    async def delete_role(self, role_id: str) -> None:
        response = await self._client.delete(
            f"/v3/access/roles/{role_id}",
            headers=self._auth_headers(),
        )
        response.raise_for_status()

    @_retry_on_401
    async def assign_role_to_user(self, user_id: str, role_id: str) -> None:
        response = await self._client.put(
            f"/v3/access/users/{user_id}",
            json={"role_id": role_id},
            headers=self._auth_headers(),
        )
        response.raise_for_status()

    @_retry_on_401
    async def get_builtin_role(self, name: str = "User") -> dict:
        """Найти встроенную роль по имени (User, Administrator, Auditor и т.д.)."""
        if name in self._builtin_role_cache:
            return self._builtin_role_cache[name]
        response = await self._client.get(
            "/v3/access/roles", headers=self._auth_headers()
        )
        response.raise_for_status()
        for role in response.json():
            if role.get("is_builtin") and role.get("name") == name:
                self._builtin_role_cache[name] = role
                return role
        raise ValueError(f"Builtin role {name!r} not found")
