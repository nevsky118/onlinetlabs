"""Templates endpoint: сборка GNS3-шаблонов для лаб.

Backend вызывает POST /v1/templates/{lab}/build в фоне перед созданием сессии.
Запускает build-скрипт, парсит UUID шаблонного проекта из stdout и возвращает его.
"""

import asyncio
import logging
import re
import sys
from asyncio.subprocess import PIPE, STDOUT
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.routers.exec import verify_internal_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/templates", tags=["templates"])

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"

# slug → build-скрипт в SCRIPTS_DIR
_BUILD_SCRIPTS: dict[str, str] = {
    "lan-static-ip": "build_lan_static_ip_template.py",
    "lan-static-ip-b": "build_lan_static_ip_template.py",
    "dhcp-basics": "build_dhcp_template.py",
    "inter-subnet-routing": "build_inter_subnet_routing_template.py",
}

_BUILD_TIMEOUT = 600.0
_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


class BuildTemplateResponse(BaseModel):
    template_project_id: str


async def _run_build(script_path: Path) -> str:
    """Запускает build-скрипт, возвращает последний UUID из stdout.

    Raises HTTPException 502/504 при ошибках.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            stdout=PIPE,
            stderr=STDOUT,
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=_BUILD_TIMEOUT)
    except TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        raise HTTPException(status_code=504, detail="Template build timed out")

    decoded = out.decode(errors="replace")

    if proc.returncode != 0:
        tail = decoded[-500:].strip()
        raise HTTPException(status_code=502, detail=f"Build script failed: {tail}")

    matches = _UUID_RE.findall(decoded)
    if not matches:
        raise HTTPException(status_code=502, detail="No template id in build output")

    return matches[-1]


@router.post(
    "/{lab}/build",
    response_model=BuildTemplateResponse,
    summary="Собрать GNS3-шаблон для лабы",
    dependencies=[Depends(verify_internal_token)],
)
async def build_template(lab: str) -> BuildTemplateResponse:
    script = _BUILD_SCRIPTS.get(lab)
    if script is None:
        raise HTTPException(status_code=404, detail=f"Unknown lab: {lab}")

    template_project_id = await _run_build(SCRIPTS_DIR / script)
    return BuildTemplateResponse(template_project_id=template_project_id)
