from urllib.parse import quote_plus

from pydantic import BaseModel, Field, field_validator


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


class LlmConfig(BaseModel):
    claude_api_key: str = Field(description="Anthropic Claude API key")
    openai_api_key: str | None = Field(
        default=None, description="OpenAI API key (optional)"
    )
    yandex_gpt_key: str | None = Field(
        default=None, description="Yandex GPT key (optional)"
    )
    default_model: str = Field(
        default="claude-sonnet-4-20250514", description="Default LLM model"
    )


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


class ConfigModel(BaseModel):
    database: DatabaseConfig
    redis: RedisConfig
    api: ApiConfig
    llm: LlmConfig
    log: LogConfig
