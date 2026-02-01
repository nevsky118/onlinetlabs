import os
from functools import lru_cache
from pathlib import Path

from config.config_model import ConfigModel
from config.encryption import decrypt_file
from config.env_config_loader import EnvConfigLoader


def _resolve_env_file() -> Path | None:
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
def _load_settings() -> ConfigModel:
    loader = EnvConfigLoader()
    env_path = _resolve_env_file()
    if env_path is None:
        return loader.load_from_environ()
    path_str = str(env_path)
    if path_str.endswith(".aes"):
        password = os.getenv("CONFIG_PASSWORD")
        if not password:
            raise OSError("CONFIG_PASSWORD env var required to decrypt .aes file")
        path_str = decrypt_file(path_str, password)
    return loader.load(path_str)


class _LazySettings:
    _instance: ConfigModel | None = None

    def __getattr__(self, name: str):
        if _LazySettings._instance is None:
            _LazySettings._instance = _load_settings()
        return getattr(_LazySettings._instance, name)


settings = _LazySettings()
__all__ = ["settings", "ConfigModel"]
