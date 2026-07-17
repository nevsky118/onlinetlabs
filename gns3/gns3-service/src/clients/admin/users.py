# GNS3 user management: create, update password, delete, search.

from ._http import _retry_on_401, _transient_retry


class UsersMixin:
    @_transient_retry
    @_retry_on_401
    async def create_user(self, username: str, password: str) -> dict:
        response = await self._client.post(
            "/v3/access/users",
            json={"username": username, "password": password},
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return response.json()

    @_retry_on_401
    async def update_user_password(self, user_id: str, new_password: str) -> None:
        response = await self._client.put(
            f"/v3/access/users/{user_id}",
            json={"password": new_password},
            headers=self._auth_headers(),
        )
        response.raise_for_status()

    @_retry_on_401
    async def delete_user(self, user_id: str) -> None:
        response = await self._client.delete(
            f"/v3/access/users/{user_id}",
            headers=self._auth_headers(),
        )
        response.raise_for_status()

    @_retry_on_401
    async def find_user_by_name(self, username: str) -> dict | None:
        """Find a user by username, otherwise None.

        Used to clean up stray student-<uid> accounts after a gns3-service
        restart (the in-memory teardown is lost, and the next launch would
        otherwise fail with 400 'already registered').
        """
        response = await self._client.get("/v3/access/users", headers=self._auth_headers())
        response.raise_for_status()
        for user in response.json():
            if user.get("username") == username:
                return user
        return None

    @_transient_retry
    @_retry_on_401
    async def get_user_token(self, username: str, password: str) -> str:
        response = await self._client.post(
            "/v3/access/users/authenticate",
            json={"username": username, "password": password},
        )
        response.raise_for_status()
        return response.json()["access_token"]
