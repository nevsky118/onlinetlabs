# GNS3 connection manager для SDK ConnectionPool.

import httpx

from onlinetlabs_mcp_sdk.connection import BaseConnectionManager
from onlinetlabs_mcp_sdk.context import SessionContext
from onlinetlabs_mcp_sdk.errors import TargetSystemConnectionError

from src.api_client import GNS3ApiClient


class GNS3ConnectionManager(BaseConnectionManager):
    """Создаёт per-student httpx.AsyncClient с JWT."""

    async def connect(self, ctx: SessionContext) -> GNS3ApiClient:
        jwt = ctx.metadata.get("gns3_jwt")
        headers = {}
        if jwt:
            headers["Authorization"] = f"Bearer {jwt}"
        client = httpx.AsyncClient(
            base_url=ctx.environment_url,
            headers=headers,
        )
        return GNS3ApiClient(client)

    async def health_check(self, connection: GNS3ApiClient) -> bool:
        """GET /v3/version — если отвечает, соединение живо."""
        try:
            version = await connection.get_version()
            return "version" in version
        except Exception:
            return False

    async def disconnect(self, connection: GNS3ApiClient) -> None:
        await connection.client.aclose()
