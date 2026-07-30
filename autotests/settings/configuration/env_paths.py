# Single place holding the env path convention. Nothing is hardcoded, paths are resolved via env_file(service), and the tier comes from ENV (local/development/ci).

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]


def env_file(service: str, tier: str | None = None) -> Path:
    """Absolute path to the service env file, deployment/<tier>/<service>.env.

    The tier defaults to ENV (as in the Makefile), otherwise local. The path is
    absolute and does not depend on the working directory.
    """
    tier = tier or os.getenv("ENV", "local")
    return _REPO_ROOT / "deployment" / tier / f"{service}.env"
