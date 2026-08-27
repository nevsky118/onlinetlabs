import json
import logging
import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from mcp_sdk.config_bootstrap import LazySettings, resolve_env_path

from config.config_model import (
    AgentsConfig,
    ApiConfig,
    ConfigModel,
    DatabaseConfig,
    GNS3Config,
    LearningAnalyticsConfig,
    LlmProvider,
    LogConfig,
    MCPConfig,
    ModelEntry,
    ObservabilityConfig,
    ProviderCreds,
    RedisConfig,
    SecurityConfig,
)
from config.llm_catalog import default_catalog
from control.criterion import BAD_REGIMES

logger = logging.getLogger(__name__)

# Required URL keys, startup is impossible without them.
_REQUIRED_URL_KEYS = (
    "FRONTEND_URL",
    "GNS3_SERVICE_URL",
    "GNS3_PUBLIC_URL",
    "GNS3_INTERNAL_URL",
    "MCP_SERVER_URL",
)


def _str2bool(value: str) -> bool:
    """Converts a string value from env into a boolean."""
    return value.strip().lower() in ("true", "1", "yes")


def build_agents_config(values: dict[str, str | None]) -> AgentsConfig:
    """Builds AgentsConfig from env: providers from secrets, catalog from code, filtered by creds."""
    # Back-compat: old AGENTS_* without the new keys → single provider.
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
            id="legacy-default",
            label=values.get("AGENTS_MODEL", "default"),
            provider_ref=ref,
            model=values.get("AGENTS_MODEL", "yandexgpt/latest"),
        )
        return AgentsConfig(
            providers={ref: creds},
            catalog=[entry],
            chat_model="legacy-default",
            intervention_model="legacy-default",
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
            chat_model,
            fallback,
        )
        chat_model = fallback

    intervention_model = values.get("AGENTS_INTERVENTION_MODEL", "yandex-gpt-5.1")
    if catalog and intervention_model not in catalog_ids:
        fallback = catalog[0].id
        logger.warning(
            "AGENTS_INTERVENTION_MODEL '%s' not in filtered catalog; falling back to '%s'",
            intervention_model,
            fallback,
        )
        intervention_model = fallback

    return AgentsConfig(
        providers=providers,
        catalog=catalog,
        chat_model=chat_model,
        intervention_model=intervention_model,
        interventions_follow_session=_str2bool(
            values.get("AGENTS_INTERVENTIONS_FOLLOW_SESSION", "false")
        ),
        temperature=float(values.get("AGENTS_TEMPERATURE", "0.3")),
        max_tokens=int(values.get("AGENTS_MAX_TOKENS", "4096")),
        request_timeout=int(values.get("AGENTS_REQUEST_TIMEOUT", "30")),
    )


def build_learning_analytics_config(values: dict[str, str | None]) -> LearningAnalyticsConfig:
    """Builds LearningAnalyticsConfig from LA_* env vars.

    Every key is optional and falls back to the Pydantic default. This is the only
    delivery route for the T_k that control/derive_thresholds.py computes.
    """
    overrides: dict[str, object] = {}

    def _take(env_key: str, field: str, cast) -> None:
        raw = values.get(env_key)
        if raw is None or raw == "":
            return
        overrides[field] = cast(raw)

    def _floats(raw: str) -> list[float]:
        return [float(part) for part in raw.split(",") if part.strip()]

    def _thresholds(raw: str) -> dict[str, float]:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("LA_DWELL_THRESHOLDS must be a JSON object of regime -> seconds")
        unknown = set(parsed) - BAD_REGIMES
        if unknown:
            raise ValueError(f"LA_DWELL_THRESHOLDS has unknown regimes: {sorted(unknown)}")
        return {regime: float(seconds) for regime, seconds in parsed.items()}

    # Cycles and the intervention switch
    _take("LA_ENABLED", "enabled", _str2bool)
    _take("LA_POLL_INTERVAL", "poll_interval", float)
    _take("LA_ANALYSIS_INTERVAL", "analysis_interval", float)
    _take("LA_COOLDOWN_PERIOD", "cooldown_period", float)
    _take("LA_PROGRESS_MAX_DURATION_HOURS", "progress_max_duration_hours", float)

    # MRT
    _take("LA_MRT_ENABLED", "mrt_enabled", _str2bool)
    _take("LA_MRT_HOLD_PROBABILITY", "mrt_hold_probability", float)
    _take("LA_MRT_T_K_JITTER_FRAC", "mrt_t_k_jitter_frac", float)

    # Research capture switches
    _take("LA_EVIDENCE_CAPTURE_ENABLED", "evidence_capture_enabled", _str2bool)
    _take("LA_LATENCY_CAPTURE_ENABLED", "latency_capture_enabled", _str2bool)
    _take("LA_GROUNDING_ABLATION_ENABLED", "grounding_ablation_enabled", _str2bool)
    _take("LA_SINGLE_AGENT_MODE", "single_agent_mode", _str2bool)
    _take("LA_SIM_LLM_HELP_ENABLED", "sim_llm_help_enabled", _str2bool)

    # Control law: T_k and the cost vector
    _take("LA_DWELL_THRESHOLDS", "dwell_thresholds", _thresholds)
    _take("LA_COST_STUCK", "cost_stuck", float)
    _take("LA_COST_INTERVENTION", "cost_intervention", float)
    _take("LA_COST_FALSE", "cost_false_intervention", float)

    # Experiment and cohort parameters
    _take("LA_ESCALATION_MAX_DWELL", "escalation_max_dwell", float)
    _take("LA_MENTOR_HANDLING_SECONDS", "mentor_handling_seconds", float)
    _take("LA_L2_INTERVENTION_CAP", "l2_intervention_cap", int)
    _take("LA_COHORT_HORIZON_DAYS", "cohort_horizon_days", float)
    _take("LA_AUTONOMY_INTERVENTION_THRESHOLD", "autonomy_intervention_threshold", int)

    # Identifier evaluation
    _take("LA_EVAL_T_K_GRID", "eval_t_k_grid", _floats)
    _take("LA_EVAL_ONSET_WINDOW_SECONDS", "eval_onset_window_seconds", float)

    return LearningAnalyticsConfig(**overrides)


def _build(values: dict[str, str | None]) -> ConfigModel:
    """Builds and validates the root configuration from a dict of environment variables."""
    # Fail-fast: check all required URL keys upfront.
    missing = [k for k in _REQUIRED_URL_KEYS if not values.get(k)]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    def _req(key: str) -> str:
        """Returns a required environment variable or raises KeyError if it's missing."""
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
    learning_analytics = build_learning_analytics_config(values)
    return ConfigModel(
        database=database,
        redis=redis,
        api=api,
        log=log,
        agents=agents,
        gns3=gns3,
        mcp=mcp,
        security=security,
        observability=observability,
        learning_analytics=learning_analytics,
    )


_PACKAGE_ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def load_settings() -> ConfigModel:
    """Loads config from ENV_FILE when set, otherwise from the process environment."""
    path = resolve_env_path(_PACKAGE_ROOT)
    return _build(dict(os.environ) if path is None else dotenv_values(path))


settings = LazySettings(load_settings)
