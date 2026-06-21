import logging
import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values

from config.config_model import (
    AgentsConfig,
    ApiConfig,
    ConfigModel,
    DatabaseConfig,
    GNS3Config,
    LlmProvider,
    LogConfig,
    MCPConfig,
    ModelEntry,
    ObservabilityConfig,
    OpenClawConfig,
    ProviderCreds,
    RedisConfig,
    SecurityConfig,
)
from config.llm_catalog import default_catalog
from tools.env_cipher import decrypt_file

logger = logging.getLogger(__name__)

# Обязательные URL-ключи — без них запуск невозможен.
_REQUIRED_URL_KEYS = (
    "FRONTEND_URL",
    "GNS3_SERVICE_URL",
    "GNS3_PUBLIC_URL",
    "GNS3_INTERNAL_URL",
    "MCP_SERVER_URL",
)


def _str2bool(value: str) -> bool:
    """Преобразует строковое значение из env в булево."""
    return value.strip().lower() in ("true", "1", "yes")


def build_agents_config(values: dict[str, str | None]) -> AgentsConfig:
    """Собирает AgentsConfig из env: провайдеры из секретов, каталог из кода, фильтр по кредам."""
    # Back-compat: старые AGENTS_* без новых ключей → одиночный провайдер.
    if values.get("AGENTS_PROVIDER") and not values.get("AGENTS_CHAT_MODEL"):
        provider = LlmProvider(values["AGENTS_PROVIDER"])
        ref = provider.value
        if provider == LlmProvider.YANDEX and not values.get("AGENTS_YANDEX_FOLDER"):
            raise ValueError("AGENTS_YANDEX_FOLDER обязателен для back-compat провайдера yandex")
        creds = ProviderCreds(
            provider=provider,
            base_url=values.get("AGENTS_BASE_URL") or None,
            api_key=values.get("AGENTS_API_KEY") or None,
            yandex_folder=values.get("AGENTS_YANDEX_FOLDER") or None,
        )
        entry = ModelEntry(
            id="legacy-default", label=values.get("AGENTS_MODEL", "default"),
            provider_ref=ref, model=values.get("AGENTS_MODEL", "yandexgpt/latest"),
        )
        return AgentsConfig(
            providers={ref: creds}, catalog=[entry],
            chat_model="legacy-default", intervention_model="legacy-default",
            temperature=float(values.get("AGENTS_TEMPERATURE", "0.3")),
            max_tokens=int(values.get("AGENTS_MAX_TOKENS", "4096")),
            request_timeout=int(values.get("AGENTS_REQUEST_TIMEOUT", "30")),
        )

    providers: dict[str, ProviderCreds] = {}
    if values.get("YANDEX_API_KEY"):
        providers["yandex"] = ProviderCreds(
            provider=LlmProvider.YANDEX,
            api_key=values["YANDEX_API_KEY"],
            yandex_folder=values.get("YANDEX_FOLDER"),
            base_url=values.get("YANDEX_BASE_URL") or None,
        )
    if values.get("OPENROUTER_API_KEY"):
        headers: dict[str, str] = {}
        if values.get("OPENROUTER_HTTP_REFERER"):
            headers["HTTP-Referer"] = values["OPENROUTER_HTTP_REFERER"]
        if values.get("OPENROUTER_TITLE"):
            headers["X-OpenRouter-Title"] = values["OPENROUTER_TITLE"]
        providers["openrouter"] = ProviderCreds(
            provider=LlmProvider.OPENAI,
            api_key=values["OPENROUTER_API_KEY"],
            base_url=values.get("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
            extra_headers=headers or None,
        )

    if not providers:
        raise ValueError(
            "Не заданы креды LLM-провайдера — установите YANDEX_API_KEY или OPENROUTER_API_KEY"
        )

    catalog = [m for m in default_catalog() if m.provider_ref in providers]

    catalog_ids = {m.id for m in catalog}

    chat_model = values.get("AGENTS_CHAT_MODEL", "yandex-gpt-5.1")
    if catalog and chat_model not in catalog_ids:
        fallback = catalog[0].id
        logger.warning(
            "AGENTS_CHAT_MODEL '%s' not in filtered catalog; falling back to '%s'",
            chat_model, fallback,
        )
        chat_model = fallback

    intervention_model = values.get("AGENTS_INTERVENTION_MODEL", "yandex-gpt-5.1")
    if catalog and intervention_model not in catalog_ids:
        fallback = catalog[0].id
        logger.warning(
            "AGENTS_INTERVENTION_MODEL '%s' not in filtered catalog; falling back to '%s'",
            intervention_model, fallback,
        )
        intervention_model = fallback

    return AgentsConfig(
        providers=providers,
        catalog=catalog,
        chat_model=chat_model,
        intervention_model=intervention_model,
        interventions_follow_session=_str2bool(values.get("AGENTS_INTERVENTIONS_FOLLOW_SESSION", "false")),
        temperature=float(values.get("AGENTS_TEMPERATURE", "0.3")),
        max_tokens=int(values.get("AGENTS_MAX_TOKENS", "4096")),
        request_timeout=int(values.get("AGENTS_REQUEST_TIMEOUT", "30")),
    )


def _build(values: dict[str, str | None]) -> ConfigModel:
    """Собирает и валидирует корневую конфигурацию из словаря переменных окружения."""
    # Fail-fast: проверяем все обязательные URL-ключи сразу.
    missing = [k for k in _REQUIRED_URL_KEYS if not values.get(k)]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    def _req(key: str) -> str:
        """Возвращает обязательную переменную окружения или падает с KeyError, если её нет."""
        v = values.get(key)
        if v is None:
            raise KeyError(f"Required env var not set: {key}")
        return v

    database = DatabaseConfig(
        user=_req("DB_USER"),
        password=_req("DB_PASSWORD"),
        host=_req("DB_HOST"),
        port=int(_req("DB_PORT")),
        db=_req("DB_NAME"),
        sql_echo=_str2bool(values.get("DB_SQL_ECHO", "false")),
    )
    redis = RedisConfig(url=_req("REDIS_URL"))
    api = ApiConfig(
        environment=_req("ENVIRONMENT"),
        debug=_str2bool(values.get("DEBUG", "false")),
        api_port=int(values.get("API_PORT", "8000")),
        frontend_url=values["FRONTEND_URL"],
        jwt_secret=_req("JWT_SECRET"),
    )
    log = LogConfig(log_level=_req("LOG_LEVEL"))
    agents = build_agents_config(values)
    openclaw = OpenClawConfig(
        enabled=_str2bool(values.get("OPENCLAW_ENABLED", "false")),
        base_url=values.get("OPENCLAW_BASE_URL") or "",  # Task 2: поле станет str|None
        token=values.get("OPENCLAW_TOKEN") or None,
        model=values.get("OPENCLAW_MODEL", "openclaw"),
        timeout_seconds=float(values.get("OPENCLAW_TIMEOUT_SECONDS", "30")),
    )
    gns3 = GNS3Config(
        service_url=values["GNS3_SERVICE_URL"],
        public_url=values["GNS3_PUBLIC_URL"],
        internal_url=values["GNS3_INTERNAL_URL"],
        node_host=values.get("GNS3_NODE_HOST", ""),
    )
    mcp = MCPConfig(
        server_url=values["MCP_SERVER_URL"],
    )
    security = SecurityConfig(
        cred_encryption_key=_req("CRED_ENCRYPTION_KEY"),
        internal_api_token=_req("INTERNAL_API_TOKEN"),
    )
    observability = ObservabilityConfig(
        retention_per_session=int(values.get("OBSERVABILITY_RETENTION_PER_SESSION", "2000")),
    )
    return ConfigModel(
        database=database,
        redis=redis,
        api=api,
        log=log,
        agents=agents,
        openclaw=openclaw,
        gns3=gns3,
        mcp=mcp,
        security=security,
        observability=observability,
    )


def _resolve_env_file() -> Path | None:
    """Определяет путь к env-файлу из ENV_FILE. Возвращает None, если переменная не задана."""
    env_file_name = os.getenv("ENV_FILE")
    if env_file_name is None:
        return None
    path = Path(env_file_name)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    if not path.exists():
        raise FileNotFoundError(f"ENV_FILE={env_file_name} not found: {path}")
    return path


@lru_cache(maxsize=1)
def load_settings() -> ConfigModel:
    """Загружает конфигурацию из окружения или env-файла, расшифровывая .aes при необходимости.

    Результат кэшируется на всё время жизни процесса.
    """
    env_path = _resolve_env_file()
    if env_path is None:
        return _build(dict(os.environ))
    path_str = str(env_path)
    if path_str.endswith(".aes"):
        password = os.getenv("CONFIG_PASSWORD")
        if not password:
            raise OSError("CONFIG_PASSWORD env var required to decrypt .aes file")
        path_str = decrypt_file(path_str, password)
    return _build(dotenv_values(path_str))


class _LazySettings:
    """Ленивый прокси к конфигурации. Загружает настройки при первом обращении к атрибуту."""

    _instance: ConfigModel | None = None

    def __getattr__(self, name: str):
        """Возвращает атрибут конфигурации, загружая её при первом доступе."""
        if _LazySettings._instance is None:
            _LazySettings._instance = load_settings()
        return getattr(_LazySettings._instance, name)


settings = _LazySettings()
