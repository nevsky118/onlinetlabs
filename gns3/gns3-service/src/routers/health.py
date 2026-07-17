# Health endpoint: checks the DB and GNS3 admin availability.

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health", tags=["health"], summary="Health check")
async def health(request: Request):
    import httpx
    from fastapi.responses import JSONResponse
    from sqlalchemy import text

    checks: dict[str, str] = {}
    overall_ok = True

    # DB
    try:
        factory = request.app.state.db_factory
        async with factory() as db:
            await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {exc.__class__.__name__}"
        overall_ok = False

    # GNS3 admin server
    try:
        from src.config import settings

        async with httpx.AsyncClient(timeout=2.0) as c:
            r = await c.get(f"{settings.gns3.url}/v3/version")
            r.raise_for_status()
        checks["gns3_server"] = "ok"
    except Exception as exc:
        checks["gns3_server"] = f"error: {exc.__class__.__name__}"
        overall_ok = False

    return JSONResponse(
        content={"status": "ok" if overall_ok else "degraded", "checks": checks},
        status_code=200 if overall_ok else 503,
    )
