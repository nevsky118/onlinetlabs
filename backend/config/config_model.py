"""Конфигурация приложения."""

from enum import Enum
from typing import Self
from urllib.parse import quote_plus

from pydantic import BaseModel, Field, field_validator, model_validator


class DatabaseConfig(BaseModel):
    """Подключение к PostgreSQL."""

    user: str = Field(description="PostgreSQL user")
    password: str = Field(description="PostgreSQL password")
    host: str = Field(description="PostgreSQL host")
    port: int = Field(description="PostgreSQL port")
    db: str = Field(description="Database name")
    sql_echo: bool = Field(default=False, description="Log SQL queries")

    @property
    def async_url(self) -> str:
        """Собирает строку подключения asyncpg из пользователя, пароля, хоста, порта и имени БД."""
        return (
            f"postgresql+asyncpg://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.db}"
        )

    @property
    def sync_url(self) -> str:
        """Собирает синхронную строку подключения psycopg из пользователя, пароля, хоста, порта и имени БД."""
        return (
            f"postgresql://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class RedisConfig(BaseModel):
    """Подключение к Redis."""

    url: str = Field(description="Redis URL (redis://...)")


class ApiConfig(BaseModel):
    """Настройки API-сервера."""

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
        """Проверяет, что окружение входит в список допустимых значений."""
        allowed = {"local", "development", "production", "test"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return v


class LogConfig(BaseModel):
    """Настройки логирования."""

    log_level: str = Field(
        description="Level: DEBUG | INFO | WARNING | ERROR | CRITICAL"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Проверяет уровень логирования и приводит его к верхнему регистру."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return upper


class LlmProvider(str, Enum):
    """Поддерживаемые LLM-провайдеры для агентов."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    YANDEX = "yandex"


class ProviderCreds(BaseModel):
    """Креды одного LLM-провайдера."""

    provider: LlmProvider
    base_url: str | None = None
    api_key: str | None = None
    yandex_folder: str | None = None
    extra_headers: dict[str, str] | None = None


class ModelEntry(BaseModel):
    """Запись каталога: выбираемая модель."""

    id: str
    label: str
    provider_ref: str
    model: str  # базовый слаг; URI строит llm/client.py
    tools: bool = True


class AgentsConfig(BaseModel):
    """Мульти-провайдерный конфиг агентов: реестр, каталог, посёрфейс-дефолты."""

    providers: dict[str, ProviderCreds]
    catalog: list[ModelEntry]
    chat_model: str
    intervention_model: str
    interventions_follow_session: bool = False
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    request_timeout: int = Field(default=30, ge=1)
    selectable_roles: set[str] = Field(
        default_factory=lambda: {"student", "instructor", "admin"}
    )

    def get_entry(self, model_id: str) -> "ModelEntry | None":
        """Найти запись каталога по id."""
        return next((m for m in self.catalog if m.id == model_id), None)

    @model_validator(mode="after")
    def validate_refs(self) -> Self:
        """Проверяет ссылки: provider_ref ∈ providers, дефолты ∈ catalog, креды достаточны."""
        ids = {m.id for m in self.catalog}
        for entry in self.catalog:
            if entry.provider_ref not in self.providers:
                raise ValueError(
                    f"ModelEntry '{entry.id}' references unknown provider '{entry.provider_ref}'"
                )
        for field in ("chat_model", "intervention_model"):
            if getattr(self, field) not in ids:
                raise ValueError(f"{field} '{getattr(self, field)}' not in catalog")
        for ref, creds in self.providers.items():
            if creds.provider in (LlmProvider.ANTHROPIC, LlmProvider.OPENAI) and not creds.api_key:
                raise ValueError(f"provider '{ref}' requires api_key")
            if creds.provider == LlmProvider.YANDEX and (not creds.api_key or not creds.yandex_folder):
                raise ValueError(f"provider '{ref}' (yandex) requires api_key and yandex_folder")
            if creds.provider == LlmProvider.OLLAMA and not creds.base_url:
                creds.base_url = "http://localhost:11434/v1"
        return self


class LearningAnalyticsConfig(BaseModel):
    """Конфигурация Learning Analytics: сбор, анализ, интервенции."""

    # Циклы
    poll_interval: float = Field(default=5.0, description="Интервал опроса MCP (сек)")
    console_poll_interval: float = Field(
        default=30.0,
        description="Интервал сверки конфигурации VPCS с заданием (сек). Каждая сверка "
        "шлёт show ip в telnet-консоль узла и видна студенту — не делать слишком частым",
    )
    analysis_interval: float = Field(default=15.0, description="Интервал анализа (сек)")
    cooldown_period: float = Field(
        default=60.0, description="Мин. пауза между интервенциями (сек)"
    )
    enabled: bool = Field(
        default=True, description="Включить интервенции (False для контрольной группы)"
    )

    # Пороги struggle-детекции
    error_repeat_threshold: int = Field(
        default=3, description="Повторов одной ошибки для срабатывания"
    )
    idle_threshold: int = Field(
        default=3, description="Кол-во idle-периодов для детекции"
    )
    entropy_threshold: float = Field(
        default=0.9, description="Порог энтропии действий (trial-and-error)"
    )
    error_freq_threshold: float = Field(
        default=2.0, description="Ошибок/мин для детекции flailing"
    )
    stuck_time_multiplier: float = Field(
        default=2.0, description="Множитель avg_latency для детекции stuck"
    )
    rate_slope_threshold: float = Field(
        default=-0.5, description="Порог slope для детекции замедления"
    )
    min_latency_floor: float = Field(
        default=30.0, description="Мин. базовая латентность для stuck (сек)"
    )
    min_idle_for_stuck: int = Field(
        default=2, description="Мин. idle-периодов для stuck"
    )

    # Параметры фичей
    idle_gap_seconds: float = Field(
        default=60.0, description="Gap > N сек = idle период"
    )
    rate_window_seconds: float = Field(
        default=120.0, description="Окно для подсчёта action rate (сек)"
    )
    min_rate_windows: int = Field(default=3, description="Мин. окон для расчёта slope")
    error_freq_window_minutes: float = Field(
        default=5.0, description="Окно частоты ошибок (мин)"
    )

    # Коллектор
    dedup_max_size: int = Field(default=10_000, description="Макс. размер dedup-кэша")
    mcp_actions_limit: int = Field(default=50, description="Лимит list_user_actions")
    mcp_logs_limit: int = Field(default=100, description="Лимит get_logs")


class OpenClawConfig(BaseModel):
    """Конфигурация OpenClaw Gateway для экспериментального бэкенда."""

    enabled: bool = Field(default=False, description="Включить бэкенд OpenClaw")
    base_url: str = Field(
        default="http://localhost:18789", description="OpenClaw Gateway URL"
    )
    token: str | None = Field(default=None, description="Bearer token для Gateway")
    model: str = Field(default="openclaw", description="Имя модели OpenClaw")
    timeout_seconds: float = Field(default=30.0, ge=1.0, description="Таймаут запроса")


class GNS3Config(BaseModel):
    """Интеграция с gns3-service и GNS3-сервером."""

    service_url: str = Field(description="Внутренний URL gns3-service")
    public_url: str = Field(description="Browser-reachable URL GNS3 Web UI для студента")
    internal_url: str = Field(description="Внутренний URL GNS3-сервера для MCP SessionContext")
    node_host: str = Field(default="", description="Host для прямых TCP-подключений к console-портам узлов (telnet VPCS). Если пусто — derive из internal_url/public_url.")


class MCPConfig(BaseModel):
    """Подключение к GNS3 MCP-серверу."""

    server_url: str = Field(description="URL GNS3 MCP-сервера")


class SecurityConfig(BaseModel):
    """Секреты приложения."""

    cred_encryption_key: str = Field(description="Fernet-ключ для шифрования GNS3-кредов")
    internal_api_token: str = Field(
        description="Shared secret for server-to-server calls (Next.js → backend /auth/exchange, backend → gns3-service /v1/exec/vtysh)"
    )


class ConfigModel(BaseModel):
    """Корневая конфигурация приложения."""

    database: DatabaseConfig
    redis: RedisConfig
    api: ApiConfig
    log: LogConfig
    agents: AgentsConfig
    learning_analytics: LearningAnalyticsConfig = Field(
        default_factory=LearningAnalyticsConfig
    )
    openclaw: OpenClawConfig = Field(default_factory=OpenClawConfig)
    gns3: GNS3Config
    mcp: MCPConfig
    security: SecurityConfig
