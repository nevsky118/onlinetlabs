# Управление ролями GNS3: кеш встроенных ролей.

from ._http import _retry_on_401


class RolesMixin:
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
