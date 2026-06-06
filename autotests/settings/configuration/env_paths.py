# Единое место с конвенцией путей env: не хардкодим, резолвим env_file(service); тир из ENV (local/development/ci).

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]


def env_file(service: str, tier: str | None = None) -> Path:
    """Абсолютный путь к env-файлу сервиса: deployment/<tier>/<service>.env.

    Тир по умолчанию из ENV (как в Makefile), иначе local. Путь абсолютный, не
    зависит от рабочей директории.
    """
    tier = tier or os.getenv("ENV", "local")
    return _REPO_ROOT / "deployment" / tier / f"{service}.env"
