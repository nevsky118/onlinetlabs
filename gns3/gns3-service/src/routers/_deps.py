# Shared FastAPI dependencies for gns3-service routers.

import secrets

from fastapi import Header, HTTPException, Request

from src.config import settings


def verify_internal_token(authorization: str | None = Header(default=None)) -> None:
    """Rejects requests without an Authorization Bearer INTERNAL_API_TOKEN.

    The only legitimate caller is the backend. Port 8101 is published, so an
    unguarded router is reachable by anything that can route to the host.
    """
    expected = settings.security.internal_api_token
    if not expected:
        raise HTTPException(status_code=503, detail="internal token not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="invalid internal token")


def get_service(request: Request):
    """Get SessionService from app.state."""
    return request.app.state.session_service


async def get_db(request: Request):
    """Open an AsyncSession via app.state.db_factory."""
    factory = request.app.state.db_factory
    if factory is None:
        raise HTTPException(status_code=503, detail="DB not configured")
    async with factory() as session:
        yield session


def get_admin_client(request: Request):
    """Get GNS3AdminClient from SessionService (for project proxy endpoints)."""
    return request.app.state.session_service._admin
