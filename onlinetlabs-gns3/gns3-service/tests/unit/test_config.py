# Юнит-тесты конфигурации gns3-service.

import pytest
from pydantic import ValidationError

from src.config.config_model import DatabaseConfig, ServiceConfig
from src.config.env_config_loader import EnvConfigLoader
from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.config]


class TestConfig:
    @autotests.num("410")
    @autotests.external_id("c1d2e3f4-0001-4ccc-dddd-410000000001")
    @autotests.name("GNS3 Service Config: DatabaseConfig.async_url формирует URL")
    def test_database_async_url(self):
        with autotests.step("Создаём DatabaseConfig и проверяем async_url"):
            db = DatabaseConfig(
                user="test_user",
                password="test_pass",
                host="localhost",
                port=5432,
                db="test_db",
            )
            assert db.async_url == (
                "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
            )

    @autotests.num("411")
    @autotests.external_id("c1d2e3f4-0002-4ccc-dddd-411000000001")
    @autotests.name("GNS3 Service Config: ServiceConfig валидирует log_level")
    def test_service_config_validates_log_level(self):
        with autotests.step("Валидный log_level приводится к upper"):
            svc = ServiceConfig(log_level="debug")
            assert svc.log_level == "DEBUG"

        with autotests.step("Невалидный log_level вызывает ValidationError"):
            with pytest.raises(ValidationError):
                ServiceConfig(log_level="INVALID")

    @autotests.num("412")
    @autotests.external_id("c1d2e3f4-0003-4ccc-dddd-412000000001")
    @autotests.name("GNS3 Service Config: EnvConfigLoader загружает из environ")
    def test_env_config_loader_from_environ(self, monkeypatch):
        with autotests.step("Устанавливаем env-переменные и загружаем конфиг"):
            env = {
                "GNS3_URL": "http://gns3:3080",
                "GNS3_ADMIN_USER": "admin",
                "GNS3_ADMIN_PASSWORD": "secret",
                "DB_USER": "u",
                "DB_PASSWORD": "p",
                "DB_HOST": "db",
                "DB_PORT": "5432",
                "DB_NAME": "mydb",
            }
            for k, v in env.items():
                monkeypatch.setenv(k, v)
            cfg = EnvConfigLoader().load_from_environ()
            assert cfg.gns3.url == "http://gns3:3080"
            assert cfg.database.db == "mydb"
            assert cfg.service.log_level == "INFO"  # default

    @autotests.num("413")
    @autotests.external_id("c1d2e3f4-0004-4ccc-dddd-413000000001")
    @autotests.name("GNS3 Service Config: _req выбрасывает KeyError при отсутствии переменной")
    def test_req_raises_key_error_for_missing(self, monkeypatch):
        with autotests.step("Загружаем из пустого dict — ожидаем KeyError"):
            for key in ("GNS3_URL", "GNS3_ADMIN_USER", "GNS3_ADMIN_PASSWORD",
                        "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"):
                monkeypatch.delenv(key, raising=False)
            with pytest.raises(KeyError, match="GNS3_URL"):
                EnvConfigLoader().load_from_environ()
