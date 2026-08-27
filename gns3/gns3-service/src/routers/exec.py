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
    project_id: str = Field(description="GNS3 project UUID")
    node_id: str = Field(description="GNS3 node UUID (must be of docker type)")
    command: str = Field(description="vtysh command without the `-c` prefix")


class VtyshResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int


_EXEC_TIMEOUT = 10.0
_DOCKER_INFRA_EXIT_CODES = frozenset({125, 126, 127})
_DOCKER_UNREACHABLE_MARKERS = (
    "cannot connect to the docker daemon",
    "permission denied while trying to connect to the docker daemon",
    "is the docker daemon running",
)


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
    summary="Run a vtysh command on an FRR node",
    description=(
        'Runs `vtysh -c "<command>"` inside the docker container of a GNS3 node '
        "and returns stdout/stderr/exit_code. Used by the backend to "
        "check OSPF neighbors, routes and other FRR configuration."
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

    exit_code = proc.returncode if proc.returncode is not None else -1
    stderr_text = stderr.decode("utf-8", errors="replace")
    lowered = stderr_text.lower()
    if exit_code in _DOCKER_INFRA_EXIT_CODES or any(
        marker in lowered for marker in _DOCKER_UNREACHABLE_MARKERS
    ):
        raise HTTPException(
            status_code=503,
            detail=f"docker exec failed before vtysh ran: {stderr_text.strip()}",
        )

    return VtyshResponse(
        stdout=stdout.decode("utf-8", errors="replace"),
        stderr=stderr_text,
        exit_code=exit_code,
    )
