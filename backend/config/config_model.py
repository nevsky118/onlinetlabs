"""Application configuration."""

from enum import Enum
from typing import Self
from urllib.parse import quote_plus

from pydantic import BaseModel, Field, field_validator, model_validator


class DatabaseConfig(BaseModel):
    """PostgreSQL connection."""

    user: str = Field(description="PostgreSQL user")
    password: str = Field(description="PostgreSQL password")
    host: str = Field(description="PostgreSQL host")
    port: int = Field(description="PostgreSQL port")
    db: str = Field(description="Database name")
    sql_echo: bool = Field(default=False, description="Log SQL queries")

    @property
    def async_url(self) -> str:
        """Builds the asyncpg connection string from user, password, host, port, and db name."""
        return (
            f"postgresql+asyncpg://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.db}"
        )

    @property
    def sync_url(self) -> str:
        """Builds the sync psycopg connection string from user, password, host, port, and db name."""
        return (
            f"postgresql://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class RedisConfig(BaseModel):
    """Redis connection."""

    url: str = Field(description="Redis URL (redis://...)")


class ApiConfig(BaseModel):
    """API server settings."""

    environment: str = Field(description="Environment: local | development | production | test")
    debug: bool = Field(default=False, description="Debug mode")
    api_port: int = Field(default=8000, description="API port")
    frontend_url: str = Field(description="Frontend URL for CORS")
    jwt_secret: str = Field(description="JWT secret for auth verification")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validates that the environment is one of the allowed values."""
        allowed = {"local", "development", "production", "test"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return v


class LogConfig(BaseModel):
    """Logging settings."""

    log_level: str = Field(description="Level: DEBUG | INFO | WARNING | ERROR | CRITICAL")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validates the log level and uppercases it."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return upper


class LlmProvider(str, Enum):
    """Supported LLM providers for agents."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    YANDEX = "yandex"


class ProviderCreds(BaseModel):
    """Credentials for a single LLM provider."""

    provider: LlmProvider
    base_url: str | None = None
    api_key: str | None = None
    yandex_folder: str | None = None
    extra_headers: dict[str, str] | None = None


class ModelEntry(BaseModel):
    """Catalog entry: a selectable model."""

    id: str
    label: str
    provider_ref: str
    model: str  # base slug; URI is built by llm/client.py
    tools: bool = True


class AgentsConfig(BaseModel):
    """Multi-provider agents config: registry, catalog, surfaced defaults."""

    providers: dict[str, ProviderCreds]
    catalog: list[ModelEntry]
    chat_model: str
    intervention_model: str
    interventions_follow_session: bool = False
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    request_timeout: int = Field(default=30, ge=1)
    selectable_roles: set[str] = Field(default_factory=lambda: {"student", "instructor", "admin"})

    def get_entry(self, model_id: str) -> "ModelEntry | None":
        """Find a catalog entry by id."""
        return next((m for m in self.catalog if m.id == model_id), None)

    @model_validator(mode="after")
    def validate_refs(self) -> Self:
        """Validates references: provider_ref ∈ providers, defaults ∈ catalog, creds are sufficient."""
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
            if creds.provider == LlmProvider.YANDEX and (
                not creds.api_key or not creds.yandex_folder
            ):
                raise ValueError(f"provider '{ref}' (yandex) requires api_key and yandex_folder")
            if creds.provider == LlmProvider.OLLAMA and not creds.base_url:
                creds.base_url = (
                    "http://localhost:11434/v1"  # Ollama runs locally, localhost is canonical
                )
        return self


class LearningAnalyticsConfig(BaseModel):
    """Learning Analytics configuration: collection, analysis, interventions."""

    # Cycles
    poll_interval: float = Field(default=5.0, description="MCP poll interval (sec)")
    analysis_interval: float = Field(default=15.0, description="Analysis interval (sec)")
    cooldown_period: float = Field(
        default=60.0, description="Min. pause between interventions (sec)"
    )
    enabled: bool = Field(
        default=True, description="Enable interventions (False for the control group)"
    )

    # MRT (micro-randomized trial): randomizes the intervene/withhold decision point
    mrt_enabled: bool = Field(
        default=False,
        description="Enable MRT randomization of decision points (otherwise OPEN/CLOSED by arm)",
    )
    mrt_hold_probability: float = Field(
        default=0.5, description="P(withhold) at an eligible point under MRT"
    )
    mrt_t_k_jitter_frac: float = Field(
        default=0.5, description="T_k jitter fraction per spell: T_k*U[1-f, 1+f]"
    )

    # Capture of raw evidence for blind labeling (disjoint from features)
    evidence_capture_enabled: bool = Field(
        default=False,
        description="Persist raw MCP observations to session_evidence_snapshots (for labeling)",
    )

    # Instrumentation of cycle stage latency (p50/p95/p99)
    latency_capture_enabled: bool = Field(
        default=False, description="Persist stage latency to cycle_latency_samples"
    )

    # Grounding ablation: generate help with and without MCP context (for the expert)
    grounding_ablation_enabled: bool = Field(
        default=False,
        description="Generate a grounded/ungrounded help pair in grounding_comparisons",
    )

    # Single-vs-multi-agent ablation: force a single generalist agent
    single_agent_mode: bool = Field(
        default=False,
        description="All interventions through a single generalist agent (multi-agent ablation)",
    )

    # Student simulation: LLM for help-request text (otherwise templates)
    sim_llm_help_enabled: bool = Field(
        default=False, description="Sim students: LLM generates help-request text (gated, budget)"
    )

    # Struggle detection thresholds
    error_repeat_threshold: int = Field(
        default=3, description="Repeats of the same error to trigger"
    )
    idle_threshold: int = Field(default=3, description="Number of idle periods for detection")
    entropy_threshold: float = Field(
        default=0.7, description="Action entropy threshold (trial-and-error)"
    )
    error_freq_threshold: float = Field(default=0.4, description="Errors/min to detect flailing")
    distinct_actuals_threshold: int = Field(
        default=2, description="Min. distinct wrong answers for trial-and-error (Table 1)"
    )
    unchanged_cycles_threshold: int = Field(
        default=3, description="Min. cycles without change for stuck (Table 1)"
    )
    stuck_time_multiplier: float = Field(
        default=2.0, description="avg_latency multiplier for stuck detection"
    )
    rate_slope_threshold: float = Field(
        default=-0.5, description="Slope threshold for slowdown detection"
    )
    min_latency_floor: float = Field(
        default=30.0, description="Min. baseline latency for stuck (sec)"
    )
    min_idle_for_stuck: int = Field(default=2, description="Min. idle periods for stuck")

    # Feature parameters
    idle_gap_seconds: float = Field(default=60.0, description="Gap > N sec = idle period")
    rate_window_seconds: float = Field(
        default=120.0, description="Window for computing action rate (sec)"
    )
    min_rate_windows: int = Field(default=3, description="Min. windows to compute slope")
    error_freq_window_minutes: float = Field(
        default=5.0, description="Error frequency window (min)"
    )

    # Progress observer
    progress_poll_interval: float = Field(
        default=25.0, description="Spec check poll interval (sec)"
    )
    progress_max_duration_hours: float = Field(
        default=12.0, description="Max. LabProgressObserver lifetime from session start (hours)"
    )

    # Collector
    dedup_max_size: int = Field(default=10_000, description="Max. dedup cache size")
    mcp_actions_limit: int = Field(default=50, description="list_user_actions limit")
    mcp_logs_limit: int = Field(default=100, description="get_logs limit")

    # Control law: dwell-time threshold in a bad regime T_k (sec) per type.
    # Default 0 = baseline (fires immediately, like the manual STRUGGLE_RULES thresholds);
    # production values are derived by minimizing J (control/derive_thresholds.py).
    dwell_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "stuck_on_step": 0.0,
            "repeating_errors": 0.0,
            "idle": 0.0,
            "trial_and_error": 0.0,
        },
        description="T_k: dwell-time threshold per regime (sec), derived from J",
    )
    # Costs for the J criterion (uniform units; the ratio is economically justified).
    cost_stuck: float = Field(
        default=1.0, description="c_stuck: cost per unit of struggle duration"
    )
    cost_intervention: float = Field(default=1.0, description="c_int: cost of one intervention")
    cost_false_intervention: float = Field(
        default=0.5, description="c_false: penalty for a false intervention"
    )

    # A/B and org metrics (Task 4)
    escalation_max_dwell: float = Field(
        default=180.0, description="Dwell threshold for objective escalation (sec)"
    )
    mentor_handling_seconds: float = Field(
        default=900.0, description="t_mentor for the hours counterfactual"
    )
    l2_intervention_cap: int = Field(
        default=0, description="Max. interventions to credit autonomy at L2"
    )

    # Task 3: cohort org metrics
    cohort_horizon_days: float = Field(
        default=30.0, description="Observation horizon T for reach-rate@T and RMST (days)"
    )
    autonomy_intervention_threshold: int = Field(
        default=0, description="Intervention threshold below which L2 counts as autonomous"
    )

    # Task 5: identifier P1 evaluation
    eval_t_k_grid: list[float] = Field(
        default=[0.0, 15.0, 30.0, 60.0, 120.0, 180.0],
        description="Grid of dwell thresholds T_k for the operating curve",
    )
    eval_onset_window_seconds: float = Field(
        default=30.0, description="Tolerance window ±Δ around struggle onset"
    )


class GNS3Config(BaseModel):
    """Integration with gns3-service and the GNS3 server."""

    service_url: str = Field(description="Internal gns3-service URL")
    public_url: str = Field(description="Browser-reachable GNS3 Web UI URL for the student")
    internal_url: str = Field(description="Internal GNS3 server URL for MCP SessionContext")
    node_host: str = Field(
        default="",
        description="Host for direct TCP connections to node console ports (telnet VPCS). If empty, derived from internal_url/public_url.",
    )


class MCPConfig(BaseModel):
    """Connection to the GNS3 MCP server."""

    server_url: str = Field(description="GNS3 MCP server URL")


class SecurityConfig(BaseModel):
    """Application secrets."""

    cred_encryption_key: str = Field(description="Fernet key for encrypting GNS3 credentials")
    internal_api_token: str = Field(
        description="Shared secret for server-to-server calls (Next.js → backend /auth/exchange, backend → gns3-service /v1/exec/vtysh)"
    )


class ObservabilityConfig(BaseModel):
    """Observability configuration: event retention, viewer roles."""

    retention_per_session: int = Field(default=2000, ge=1)
    viewer_roles: set[str] = Field(default_factory=lambda: {"instructor", "admin"})


class ConfigModel(BaseModel):
    """Root application configuration."""

    database: DatabaseConfig
    redis: RedisConfig
    api: ApiConfig
    log: LogConfig
    agents: AgentsConfig
    learning_analytics: LearningAnalyticsConfig = Field(default_factory=LearningAnalyticsConfig)
    gns3: GNS3Config
    mcp: MCPConfig
    security: SecurityConfig
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
