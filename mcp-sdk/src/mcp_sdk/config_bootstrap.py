"""Shared env-file resolution and lazy settings loading.

Each service keeps its own config model and `_build`; only the bootstrap around
them is shared, since all three had a verbatim copy of it.
"""

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcp_sdk.env_cipher import decrypt_file


def resolve_env_file(package_root: Path) -> Path | None:
    """Path from ENV_FILE, resolved relative to the package root. None if unset."""
    env_file_name = os.getenv("ENV_FILE")
    if env_file_name is None:
        return None
    path = Path(env_file_name)
    if not path.is_absolute():
        path = package_root / path
    if not path.exists():
        raise FileNotFoundError(f"ENV_FILE={env_file_name} not found: {path}")
    return path


def resolve_env_path(package_root: Path) -> str | None:
    """Readable env-file path, decrypting a .aes into a temp file first."""
    env_path = resolve_env_file(package_root)
    if env_path is None:
        return None
    path_str = str(env_path)
    if path_str.endswith(".aes"):
        password = os.getenv("CONFIG_PASSWORD")
        if not password:
            raise OSError("CONFIG_PASSWORD env var required to decrypt .aes file")
        path_str = decrypt_file(path_str, password)
    return path_str


class LazySettings:
    """Proxy that loads settings on first attribute access.

    Deferred so importing a module does not require a complete environment,
    which is what makes the test suites able to import config-dependent code.
    """

    def __init__(self, loader: Callable[[], Any]) -> None:
        self._loader = loader
        self._instance: Any | None = None

    def __getattr__(self, name: str):
        if name in ("_loader", "_instance"):
            raise AttributeError(name)
        if self._instance is None:
            self._instance = self._loader()
        return getattr(self._instance, name)
