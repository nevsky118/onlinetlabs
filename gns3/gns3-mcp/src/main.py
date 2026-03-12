# Entry point для GNS3 MCP Server.

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

pool = ConnectionPool(manager=GNS3ConnectionManager(), max_size=settings.pool.max_size)
log_buffer = LogBuffer(
    max_entries=settings.log_buffer.max_entries,
    inactivity_timeout=settings.log_buffer.inactivity_timeout,
)

impl = GNS3Server(pool=pool, log_buffer=log_buffer, history_url=settings.gns3_service_url)
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


register_domain_tools(server, _get_client, _get_project_id)


def main() -> None:
    logger.info(
        "GNS3 MCP Server starting on %s:%s",
        settings.mcp.host,
        settings.mcp.port,
    )
    server.run(transport=settings.mcp.transport)


if __name__ == "__main__":
    main()
