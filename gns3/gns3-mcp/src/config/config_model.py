# Модели конфигурации GNS3 MCP Server.

from typing import Literal

from pydantic import BaseModel, Field


class MCPConfig(BaseModel):
    server_name: str = Field(default="gns3")
    transport: Literal["streamable-http", "stdio"] = Field(default="streamable-http")
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8100)


class PoolConfig(BaseModel):
    """Пул per-(environment_url, user_id) соединений к GNS3.

    max_size — потолок ОДНОВРЕМЕННО живых соединений (не всех обслуженных юзеров):
    простаивающие закрываются по idle_ttl, при нехватке места вытесняется LRU.
    """

    max_size: int = Field(default=200, description="Потолок одновременных соединений")
    idle_ttl: float = Field(default=600.0, description="Закрывать соединение после N сек простоя")
    health_check_interval: float = Field(
        default=60.0, description="Не чаще N сек проверять живость соединения из кеша"
    )
    min_evict_idle: float = Field(
        default=30.0, description="Вытеснять LRU, только если оно простаивало N сек"
    )


class LogBufferConfig(BaseModel):
    max_entries: int = Field(default=500)
    inactivity_timeout: float = Field(default=300.0)


class GNS3MCPConfigModel(BaseModel):
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    pool: PoolConfig = Field(default_factory=PoolConfig)
    log_buffer: LogBufferConfig = Field(default_factory=LogBufferConfig)
    gns3_service_url: str = Field(default="http://localhost:8101")
