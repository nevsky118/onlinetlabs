# Конфигурация GNS3 MCP Server: lazy settings loader.

import os
from functools import lru_cache
from pathlib import Path

from src.config.config_model import GNS3MCPConfigModel
from src.config.encryption import decrypt_file
from src.config.env_config_loader import EnvConfigLoader


def _resolve_env_file() -> Path | None:
    env_file_name = os.getenv("ENV_FILE")
    if env_file_name is None:
        return None
    path = Path(env_file_name)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent.parent / path
    if not path.exists():
        raise FileNotFoundError(f"ENV_FILE={env_file_name} not found: {path}")
    return path


@lru_cache(maxsize=1)
def _load_settings() -> GNS3MCPConfigModel:
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
    def __getattr__(self, name: str):
        return getattr(_load_settings(), name)


settings = _LazySettings()
__all__ = ["settings", "GNS3MCPConfigModel"]
