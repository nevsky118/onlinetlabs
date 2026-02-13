import pytest

from config.config_model import (
    ApiConfig,
    ConfigModel,
    DatabaseConfig,
    LlmConfig,
    LogConfig,
    RedisConfig,
)

pytestmark = [pytest.mark.unit, pytest.mark.config]


class TestDatabaseConfig:
    def test_async_url_escapes_special_chars(self):
        cfg = DatabaseConfig(
            user="admin", password="p@ss:word", host="localhost", port=5432, db="test"
        )
        assert "p%40ss%3Aword" in cfg.async_url
        assert cfg.async_url.startswith("postgresql+asyncpg://")

    def test_sync_url(self):
        cfg = DatabaseConfig(user="u", password="p", host="h", port=5432, db="d")
        assert cfg.sync_url == "postgresql://u:p@h:5432/d"

    def test_sql_echo_defaults_false(self):
        cfg = DatabaseConfig(user="u", password="p", host="h", port=5432, db="d")
        assert cfg.sql_echo is False


class TestApiConfig:
    def test_valid_environment(self):
        cfg = ApiConfig(environment="local", jwt_secret="s")
        assert cfg.environment == "local"

    def test_invalid_environment_raises(self):
        with pytest.raises(ValueError, match="ENVIRONMENT"):
            ApiConfig(environment="staging", jwt_secret="s")

    def test_defaults(self):
        cfg = ApiConfig(environment="test", jwt_secret="s")
        assert cfg.debug is False
        assert cfg.api_port == 8000


class TestLogConfig:
    def test_normalizes_to_uppercase(self):
        cfg = LogConfig(log_level="info")
        assert cfg.log_level == "INFO"

    def test_invalid_level_raises(self):
        with pytest.raises(ValueError, match="LOG_LEVEL"):
            LogConfig(log_level="TRACE")


class TestLlmConfig:
    def test_optional_keys(self):
        cfg = LlmConfig(claude_api_key="sk-ant-xxx")
        assert cfg.openai_api_key is None
        assert cfg.yandex_gpt_key is None

    def test_default_model(self):
        cfg = LlmConfig(claude_api_key="sk-ant-xxx")
        assert "claude" in cfg.default_model


class TestConfigModel:
    def test_full_config(self):
        cfg = ConfigModel(
            database=DatabaseConfig(
                user="u", password="p", host="h", port=5432, db="d"
            ),
            redis=RedisConfig(url="redis://localhost:6379/0"),
            api=ApiConfig(environment="test", jwt_secret="s"),
            llm=LlmConfig(claude_api_key="sk-ant-xxx"),
            log=LogConfig(log_level="DEBUG"),
        )
        assert cfg.database.host == "h"
        assert cfg.api.environment == "test"
