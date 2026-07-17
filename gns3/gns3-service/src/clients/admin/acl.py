# GNS3 ACL management.

from ._http import _retry_on_401, _transient_retry


class AclMixin:
    @_transient_retry
    @_retry_on_401
    async def create_acl(self, path: str, role_id: str, user_id: str, allowed: bool = True) -> dict:
        response = await self._client.post(
            "/v3/access/acl",
            json={
                "path": path,
                "role_id": role_id,
                "user_id": user_id,
                "ace_type": "user",
                "allowed": allowed,
            },
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response.json()
