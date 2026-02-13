import pytest

from config.config_model import ConfigModel
from config.env_config_loader import EnvConfigLoader

pytestmark = [pytest.mark.unit, pytest.mark.config]

_FULL_ENV = {
    "DB_USER": "postgres",
    "DB_PASSWORD": "secret",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "onlinetlabs",
    "REDIS_URL": "redis://localhost:6379/0",
    "ENVIRONMENT": "test",
    "FRONTEND_URL": "http://localhost:3000",
    "JWT_SECRET": "test-secret",
    "CLAUDE_API_KEY": "sk-ant-test",
    "LOG_LEVEL": "DEBUG",
}


class TestEnvConfigLoader:
    def test_build_from_dict(self):
        loader = EnvConfigLoader()
        cfg = loader._build(_FULL_ENV)
        assert isinstance(cfg, ConfigModel)
        assert cfg.database.host == "localhost"
        assert cfg.api.environment == "test"
        assert cfg.llm.claude_api_key == "sk-ant-test"

    def test_missing_required_key_raises(self):
        loader = EnvConfigLoader()
        incomplete = {k: v for k, v in _FULL_ENV.items() if k != "DB_HOST"}
        with pytest.raises(KeyError, match="DB_HOST"):
            loader._build(incomplete)

    def test_optional_keys_default_to_none(self):
        loader = EnvConfigLoader()
        cfg = loader._build(_FULL_ENV)
        assert cfg.llm.openai_api_key is None

    def test_sql_echo_str2bool(self):
        env = {**_FULL_ENV, "DB_SQL_ECHO": "true"}
        loader = EnvConfigLoader()
        cfg = loader._build(env)
        assert cfg.database.sql_echo is True

    def test_load_from_environ(self, monkeypatch):
        for k, v in _FULL_ENV.items():
            monkeypatch.setenv(k, v)
        loader = EnvConfigLoader()
        cfg = loader.load_from_environ()
        assert cfg.database.db == "onlinetlabs"

    def test_load_from_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("\n".join(f"{k}={v}" for k, v in _FULL_ENV.items()))
        loader = EnvConfigLoader()
        cfg = loader.load(str(env_file))
        assert cfg.api.environment == "test"
