"""Exec endpoint: runs commands inside GNS3 docker nodes. Used to poll FRR.

POST /v1/exec/vtysh resolves properties.container_id via the admin client, then
runs `docker exec <container_id> vtysh -c "<command>"` over the local docker.sock
and returns stdout/stderr/exit_code.
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.routers._deps import verify_internal_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/exec", tags=["exec"])


class VtyshRequest(BaseModel):
    project_id: str = Field(description="UUID проекта GNS3")
    node_id: str = Field(description="UUID узла GNS3 (должен быть docker-типа)")
    command: str = Field(description="vtysh-команда без префикса `-c`")


class VtyshResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int


_EXEC_TIMEOUT = 10.0


async def _fetch_container_id(admin_client, project_id: str, node_id: str) -> str:
    """Look up a node's docker container_id via the GNS3 admin API."""
    response = await admin_client.request(
        "GET",
        f"/v3/projects/{project_id}/nodes/{node_id}",
    )
    if response.status_code == 404:
        raise HTTPException(
            status_code=404, detail=f"node {node_id} not found in project {project_id}"
        )
    response.raise_for_status()
    payload = response.json()
    if payload.get("node_type") != "docker":
        raise HTTPException(
            status_code=400,
            detail=f"node {node_id} is {payload.get('node_type')!r}, only docker nodes support exec",
        )
    container_id = (payload.get("properties") or {}).get("container_id")
    if not container_id:
        raise HTTPException(
            status_code=409,
            detail=f"node {node_id} has no container_id (not started?)",
        )
    return container_id


@router.post(
    "/vtysh",
    response_model=VtyshResponse,
    summary="Выполнить vtysh-команду на FRR-узле",
    description=(
        'Запускает `vtysh -c "<command>"` внутри docker-контейнера узла GNS3 '
        "и возвращает stdout/stderr/exit_code. Используется backend'ом для "
        "проверки OSPF-соседей, маршрутов и прочей FRR-конфигурации."
    ),
    dependencies=[Depends(verify_internal_token)],
)
async def exec_vtysh(req: VtyshRequest, request: Request) -> VtyshResponse:
    service = request.app.state.session_service
    admin_client = service._admin

    container_id = await _fetch_container_id(admin_client, req.project_id, req.node_id)

    try:
        async with asyncio.timeout(_EXEC_TIMEOUT):
            proc = await asyncio.create_subprocess_exec(
                "docker",
                "exec",
                container_id,
                "vtysh",
                "-c",
                req.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
    except TimeoutError:
        raise HTTPException(status_code=504, detail=f"vtysh exec timed out after {_EXEC_TIMEOUT}s")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="docker CLI not available inside gns3-service")

    return VtyshResponse(
        stdout=stdout.decode("utf-8", errors="replace"),
        stderr=stderr.decode("utf-8", errors="replace"),
        exit_code=proc.returncode if proc.returncode is not None else -1,
    )
