# GNS3 connection manager for SDK ConnectionPool.

import httpx
from mcp_sdk.connection import BaseConnectionManager
from mcp_sdk.context import SessionContext

from src.api_client import GNS3ApiClient


class GNS3ConnectionManager(BaseConnectionManager):
    """Creates a per-student httpx.AsyncClient with JWT."""

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
        """Connection is alive if GET /v3/version responds."""
        try:
            version = await connection.get_version()
            return "version" in version
        except Exception:
            return False

    async def disconnect(self, connection: GNS3ApiClient) -> None:
        await connection.client.aclose()
