# Загрузчик конфигурации из переменных окружения.

import os

from dotenv import dotenv_values

from src.config.config_model import (
    GNS3MCPConfigModel,
    LogBufferConfig,
    MCPConfig,
    PoolConfig,
)


class EnvConfigLoader:
    def load(self, env_path: str) -> GNS3MCPConfigModel:
        values = dotenv_values(env_path)
        return self._build(values)

    def load_from_environ(self) -> GNS3MCPConfigModel:
        return self._build(dict(os.environ))

    @staticmethod
    def _build(values: dict[str, str | None]) -> GNS3MCPConfigModel:
        mcp = MCPConfig(
            server_name=values.get("MCP_SERVER_NAME", "gns3"),
            transport=values.get("MCP_TRANSPORT", "streamable-http"),
            host=values.get("MCP_HOST", "127.0.0.1"),
            port=int(values.get("MCP_PORT", "8100")),
        )
        pool = PoolConfig(max_size=int(values.get("POOL_MAX_SIZE", "50")))
        log_buffer = LogBufferConfig(
            max_entries=int(values.get("LOG_BUFFER_MAX_ENTRIES", "500")),
            inactivity_timeout=float(
                values.get("LOG_BUFFER_INACTIVITY_TIMEOUT", "300.0")
            ),
        )
        return GNS3MCPConfigModel(
            mcp=mcp,
            pool=pool,
            log_buffer=log_buffer,
            gns3_service_url=values.get("GNS3_SERVICE_URL", "http://localhost:8101"),
        )
