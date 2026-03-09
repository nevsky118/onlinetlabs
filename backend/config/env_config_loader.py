import os

from dotenv import dotenv_values

from config.config_model import (
    AgentsConfig,
    ApiConfig,
    ConfigModel,
    DatabaseConfig,
    LogConfig,
    RedisConfig,
)


def _str2bool(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes")


class EnvConfigLoader:
    def load(self, env_path: str) -> ConfigModel:
        values = dotenv_values(env_path)
        return self._build(values)

    def load_from_environ(self) -> ConfigModel:
        return self._build(dict(os.environ))

    @staticmethod
    def _build(values: dict[str, str | None]) -> ConfigModel:
        def _req(key: str) -> str:
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
            frontend_url=values.get("FRONTEND_URL", "http://localhost:3000"),
            jwt_secret=_req("JWT_SECRET"),
        )
        log = LogConfig(log_level=_req("LOG_LEVEL"))
        agents = AgentsConfig(
            provider=values.get("AGENTS_PROVIDER", "anthropic"),
            model=values.get("AGENTS_MODEL", "claude-sonnet-4-20250514"),
            base_url=values.get("AGENTS_BASE_URL") or None,
            api_key=values.get("AGENTS_API_KEY") or None,
            temperature=float(values.get("AGENTS_TEMPERATURE", "0.3")),
            max_tokens=int(values.get("AGENTS_MAX_TOKENS", "4096")),
            request_timeout=int(values.get("AGENTS_REQUEST_TIMEOUT", "30")),
        )
        return ConfigModel(
            database=database, redis=redis, api=api, log=log, agents=agents
        )
