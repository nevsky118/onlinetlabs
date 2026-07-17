# Shared FastAPI dependencies for gns3-service routers.

from fastapi import HTTPException, Request


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
