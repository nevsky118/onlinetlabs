import os

from dotenv import dotenv_values

from config.config_model import (
    ApiConfig,
    ConfigModel,
    DatabaseConfig,
    LlmConfig,
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
        llm = LlmConfig(
            claude_api_key=_req("CLAUDE_API_KEY"),
            openai_api_key=values.get("OPENAI_API_KEY") or None,
            yandex_gpt_key=values.get("YANDEX_GPT_KEY") or None,
            default_model=values.get("DEFAULT_LLM_MODEL", "claude-sonnet-4-20250514"),
        )
        log = LogConfig(log_level=_req("LOG_LEVEL"))
        return ConfigModel(database=database, redis=redis, api=api, llm=llm, log=log)
