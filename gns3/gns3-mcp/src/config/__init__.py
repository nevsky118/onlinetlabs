# GNS3 MCP Server configuration: lazy settings loader.

from functools import lru_cache
from pathlib import Path

from mcp_sdk.config_bootstrap import LazySettings, resolve_env_path

from src.config.config_model import GNS3MCPConfigModel
from src.config.env_config_loader import EnvConfigLoader

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


@lru_cache(maxsize=1)
def _load_settings() -> GNS3MCPConfigModel:
    loader = EnvConfigLoader()
    path = resolve_env_path(_PACKAGE_ROOT)
    return loader.load_from_environ() if path is None else loader.load(path)


settings = LazySettings(_load_settings)
__all__ = ["GNS3MCPConfigModel", "settings"]
