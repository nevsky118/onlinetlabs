"""Liveness and readiness endpoints."""

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from config import settings
from kit.db import async_session
from kit.redis import redis_client

router = APIRouter(tags=["health"])

_DEEP_TIMEOUT = 2.0


class HealthResponse(BaseModel):
    """Process liveness."""

    status: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Instant process liveness check. No external calls."""
    return HealthResponse(status="ok")


async def _check_db() -> str:
    """One trivial query against the database."""
    async with async_session() as db:
        await db.execute(text("SELECT 1"))
    return "ok"


async def _check_redis() -> str:
    """A ping against Redis."""
    client = redis_client(decode_responses=False)
    try:
        await client.ping()
    finally:
        await client.aclose()
    return "ok"


async def _check_gns3() -> str:
    """The gns3-service health endpoint."""
    async with httpx.AsyncClient(timeout=_DEEP_TIMEOUT) as client:
        response = await client.get(f"{settings.gns3.service_url}/health")
        response.raise_for_status()
    return "ok"


@router.get("/health/deep")
async def health_deep() -> JSONResponse:
    """Dependency check for readiness probes and alerts.

    Answers 503 on a failure so an orchestrator takes the pod out of rotation
    without killing it, and a temporary dependency dip does not cascade.
    """
    checks: dict[str, str] = {}
    healthy = True
    for name, probe in (("db", _check_db), ("redis", _check_redis), ("gns3_service", _check_gns3)):
        try:
            checks[name] = await probe()
        except Exception as exc:
            checks[name] = f"error: {exc.__class__.__name__}"
            healthy = False

    return JSONResponse(
        content={"status": "ok" if healthy else "degraded", "checks": checks},
        status_code=200 if healthy else 503,
    )
