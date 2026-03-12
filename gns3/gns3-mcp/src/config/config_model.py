# Модели конфигурации GNS3 MCP Server.

from typing import Literal

from pydantic import BaseModel, Field


class MCPConfig(BaseModel):
    server_name: str = Field(default="gns3")
    transport: Literal["streamable-http", "stdio"] = Field(default="streamable-http")
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8100)


class PoolConfig(BaseModel):
    max_size: int = Field(default=50)


class LogBufferConfig(BaseModel):
    max_entries: int = Field(default=500)
    inactivity_timeout: float = Field(default=300.0)


class GNS3MCPConfigModel(BaseModel):
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    pool: PoolConfig = Field(default_factory=PoolConfig)
    log_buffer: LogBufferConfig = Field(default_factory=LogBufferConfig)
    gns3_service_url: str = Field(default="http://localhost:8101")
