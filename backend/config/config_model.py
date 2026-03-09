from enum import Enum
from typing import Self
from urllib.parse import quote_plus

from pydantic import BaseModel, Field, field_validator, model_validator


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

    @property
    def sync_url(self) -> str:
        return (
            f"postgresql://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class RedisConfig(BaseModel):
    url: str = Field(description="Redis URL (redis://...)")


class ApiConfig(BaseModel):
    environment: str = Field(
        description="Environment: local | development | production | test"
    )
    debug: bool = Field(default=False, description="Debug mode")
    api_port: int = Field(default=8000, description="API port")
    frontend_url: str = Field(
        default="http://localhost:3000", description="Frontend URL for CORS"
    )
    jwt_secret: str = Field(description="JWT secret for auth verification")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"local", "development", "production", "test"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return v


class LogConfig(BaseModel):
    log_level: str = Field(
        description="Level: DEBUG | INFO | WARNING | ERROR | CRITICAL"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return upper


class LlmProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"


class AgentsConfig(BaseModel):
    provider: LlmProvider = LlmProvider.ANTHROPIC
    model: str = Field(default="claude-sonnet-4-20250514")
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    request_timeout: int = Field(default=30, ge=1)

    @model_validator(mode="after")
    def validate_provider_requirements(self) -> Self:
        if self.provider in (LlmProvider.ANTHROPIC, LlmProvider.OPENAI) and not self.api_key:
            raise ValueError(f"api_key required for provider '{self.provider.value}'")
        if self.provider == LlmProvider.OLLAMA and not self.base_url:
            self.base_url = "http://localhost:11434/v1"
        return self


class ConfigModel(BaseModel):
    database: DatabaseConfig
    redis: RedisConfig
    api: ApiConfig
    log: LogConfig
    agents: AgentsConfig
