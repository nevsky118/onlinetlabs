# Загрузчик конфигурации из переменных окружения.

import os

from dotenv import dotenv_values

from src.config.config_model import (
    DatabaseConfig,
    GNS3Config,
    GNS3ServiceConfigModel,
    RedisConfig,
    SecurityConfig,
    ServiceConfig,
)


def _str2bool(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes")


class EnvConfigLoader:
    def load(self, env_path: str) -> GNS3ServiceConfigModel:
        values = dotenv_values(env_path)
        return self._build(values)

    def load_from_environ(self) -> GNS3ServiceConfigModel:
        return self._build(dict(os.environ))

    @staticmethod
    def _build(values: dict[str, str | None]) -> GNS3ServiceConfigModel:
        def _req(key: str) -> str:
            value = values.get(key)
            if value is None:
                raise KeyError(f"Required env var not set: {key}")
            return value

        gns3_url = _req("GNS3_URL")
        gns3 = GNS3Config(
            url=gns3_url,
            public_url=values.get("GNS3_PUBLIC_URL", gns3_url),
            admin_user=_req("GNS3_ADMIN_USER"),
            admin_password=_req("GNS3_ADMIN_PASSWORD"),
        )
        database = DatabaseConfig(
            user=_req("DB_USER"),
            password=_req("DB_PASSWORD"),
            host=_req("DB_HOST"),
            port=int(_req("DB_PORT")),
            db=_req("DB_NAME"),
            sql_echo=_str2bool(values.get("DB_SQL_ECHO", "false")),
        )
        service = ServiceConfig(
            host=values.get("SERVICE_HOST", "127.0.0.1"),
            port=int(values.get("SERVICE_PORT", "8101")),
            log_level=values.get("LOG_LEVEL", "INFO"),
        )
        redis = RedisConfig(url=_req("REDIS_URL"))
        security = SecurityConfig(internal_api_token=_req("INTERNAL_API_TOKEN"))
        return GNS3ServiceConfigModel(
            gns3=gns3,
            database=database,
            service=service,
            redis=redis,
            security=security,
        )
