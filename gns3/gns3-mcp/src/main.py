# Entry point for GNS3 MCP Server.

import logging

from mcp_sdk.connection import ConnectionPool
from mcp_sdk.server import OnlinetlabsMCPServer

from src.config import settings
from src.connection import GNS3ConnectionManager
from src.domain_tools import register_domain_tools
from src.log_buffer import LogBuffer
from src.server import GNS3Server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pool = ConnectionPool(
    manager=GNS3ConnectionManager(),
    max_size=settings.pool.max_size,
    idle_ttl=settings.pool.idle_ttl,
    health_check_interval=settings.pool.health_check_interval,
    min_evict_idle=settings.pool.min_evict_idle,
)


def _new_log_buffer() -> LogBuffer:
    """One buffer per (user, project); the server owns the keying."""
    return LogBuffer(
        max_entries=settings.log_buffer.max_entries,
        inactivity_timeout=settings.log_buffer.inactivity_timeout,
    )


impl = GNS3Server(
    pool=pool,
    history_url=settings.gns3_service_url,
    internal_api_token=settings.internal_api_token,
    log_buffer_factory=_new_log_buffer,
)
server = OnlinetlabsMCPServer(
    name=settings.mcp.server_name,
    implementation=impl,
    host=settings.mcp.host,
    port=settings.mcp.port,
)


async def _get_client(ctx):
    return await pool.get_connection(ctx)


def _get_project_id(ctx):
    return impl._project_id(ctx)


register_domain_tools(
    server,
    _get_client,
    _get_project_id,
    service_url=settings.gns3_service_url,
    internal_api_token=settings.internal_api_token,
)


def main() -> None:
    logger.info(
        "GNS3 MCP Server starting on %s:%s",
        settings.mcp.host,
        settings.mcp.port,
    )
    server.run(transport=settings.mcp.transport)


if __name__ == "__main__":
    main()
