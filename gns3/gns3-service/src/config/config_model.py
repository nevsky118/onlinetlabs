# Pydantic-модели конфигурации gns3-service.

from urllib.parse import quote_plus

from pydantic import BaseModel, Field, field_validator


class GNS3Config(BaseModel):
    url: str = Field(description="GNS3 server URL (internal, used by gns3-service)")
    public_url: str = Field(
        description="GNS3 server URL exposed to end-user browsers (deep-links, creds dialog)"
    )
    admin_user: str = Field(description="GNS3 admin username")
    admin_password: str = Field(description="GNS3 admin password")


class DatabaseConfig(BaseModel):
    user: str = Field(description="PostgreSQL user")
    password: str = Field(description="PostgreSQL password")
    host: str = Field(description="PostgreSQL host")
    port: int = Field(description="PostgreSQL port")
    db: str = Field(description="Database name")
    sql_echo: bool = Field(default=False, description="Log SQL queries")

    @property
    def async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class RedisConfig(BaseModel):
    url: str = Field(description="Redis URL (redis://...)")


class ServiceConfig(BaseModel):
    host: str = Field(default="127.0.0.1", description="Service host")
    port: int = Field(default=8101, description="Service port")
    log_level: str = Field(default="INFO", description="Log level")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return upper


class SecurityConfig(BaseModel):
    """Shared-secret config for server-to-server auth (backend → gns3-service)."""

    internal_api_token: str = Field(description="Shared bearer token required on /v1/exec/vtysh")


class GNS3ServiceConfigModel(BaseModel):
    gns3: GNS3Config
    database: DatabaseConfig
    service: ServiceConfig
    redis: RedisConfig
    security: SecurityConfig
