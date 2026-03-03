# Pydantic-модели конфигурации gns3-service.

from urllib.parse import quote_plus

from pydantic import BaseModel, Field, field_validator


class GNS3Config(BaseModel):
    url: str = Field(description="GNS3 server URL")
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


class GNS3ServiceConfigModel(BaseModel):
    gns3: GNS3Config
    database: DatabaseConfig
    service: ServiceConfig
