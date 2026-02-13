import pytest

from tests.report import autotests

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


class TestLazySettings:
    def test_settings_loads_from_environ(self, monkeypatch):
        for k, v in _FULL_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("ENV_FILE", raising=False)

        from app.config import _load_settings, _LazySettings

        _load_settings.cache_clear()
        _LazySettings._instance = None

        from app.config import settings

        assert settings.database.host == "localhost"
        assert isinstance(settings.api, object)

    def test_settings_loads_from_env_file(self, tmp_path, monkeypatch):
        env_file = tmp_path / "test.env"
        env_file.write_text("\n".join(f"{k}={v}" for k, v in _FULL_ENV.items()))
        monkeypatch.setenv("ENV_FILE", str(env_file))

        from app.config import _load_settings, _LazySettings

        _load_settings.cache_clear()
        _LazySettings._instance = None

        from app.config import settings

        assert settings.database.db == "onlinetlabs"

    def test_resolve_env_file_missing_raises(self, monkeypatch):
        monkeypatch.setenv("ENV_FILE", "/nonexistent/path.env")

        from app.config import _load_settings, _LazySettings

        _load_settings.cache_clear()
        _LazySettings._instance = None

        with pytest.raises(FileNotFoundError):
            from app.config import _resolve_env_file

            _resolve_env_file()


class TestResolveEnvFile:
    @autotests.num("60")
    @autotests.external_id("727a8649-0e57-405a-81af-7978e37be803")
    @autotests.name("resolve_env_file: относительный путь разрешается от корня проекта")
    def test_resolve_relative_env_file(self, monkeypatch):
        """Проверяет что относительный ENV_FILE разрешается от корня проекта."""
        # Arrange — local.env.example exists at project root
        monkeypatch.setenv("ENV_FILE", "local.env.example")

        from app.config import _resolve_env_file

        # Act
        with autotests.step("Вызываем _resolve_env_file с относительным путём"):
            result = _resolve_env_file()

        # Assert
        with autotests.step("Проверяем что путь абсолютный и существует"):
            assert result is not None
            assert result.is_absolute()
            assert result.exists()
            assert result.name == "local.env.example"


class TestAesDecryptPath:
    @autotests.num("61")
    @autotests.external_id("25e4d598-0042-42ea-af03-32dddbde58e5")
    @autotests.name("load_settings: дешифрует .aes файл")
    def test_load_settings_decrypts_aes(self, tmp_path, monkeypatch):
        """Проверяет что _load_settings дешифрует .aes файл при наличии CONFIG_PASSWORD."""
        from app.config.encryption import encrypt_file

        # Arrange
        env_file = tmp_path / "test.env"
        env_content = "\n".join(f"{k}={v}" for k, v in _FULL_ENV.items())
        env_file.write_text(env_content)

        password = "test-aes-password"
        with autotests.step("Шифруем .env файл"):
            encrypted_path = encrypt_file(str(env_file), password)

        monkeypatch.setenv("ENV_FILE", encrypted_path)
        monkeypatch.setenv("CONFIG_PASSWORD", password)

        from app.config import _load_settings, _LazySettings

        _load_settings.cache_clear()
        _LazySettings._instance = None

        # Act
        with autotests.step("Вызываем _load_settings с .aes файлом"):
            cfg = _load_settings()

        # Assert
        with autotests.step("Проверяем что настройки загружены"):
            assert cfg.database.host == "localhost"
            assert cfg.api.jwt_secret == "test-secret"

    @autotests.num("62")
    @autotests.external_id("5c73604a-5ad7-4f82-aae9-b9f65583c0b6")
    @autotests.name("load_settings: .aes без CONFIG_PASSWORD вызывает OSError")
    def test_load_settings_aes_no_password(self, tmp_path, monkeypatch):
        """Проверяет что .aes без CONFIG_PASSWORD вызывает OSError."""
        from app.config.encryption import encrypt_file

        # Arrange
        env_file = tmp_path / "test.env"
        env_file.write_text("\n".join(f"{k}={v}" for k, v in _FULL_ENV.items()))
        encrypted_path = encrypt_file(str(env_file), "somepass")

        monkeypatch.setenv("ENV_FILE", encrypted_path)
        monkeypatch.delenv("CONFIG_PASSWORD", raising=False)

        from app.config import _load_settings, _LazySettings

        _load_settings.cache_clear()
        _LazySettings._instance = None

        # Act & Assert
        with autotests.step("Вызываем _load_settings без CONFIG_PASSWORD"):
            with pytest.raises(OSError, match="CONFIG_PASSWORD"):
                _load_settings()
