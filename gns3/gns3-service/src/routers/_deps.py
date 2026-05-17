# Общие FastAPI-зависимости для роутеров gns3-service.

from fastapi import HTTPException, Request


def get_service(request: Request):
    """Достать SessionService из app.state."""
    return request.app.state.session_service


async def get_db(request: Request):
    """Открыть AsyncSession через app.state.db_factory."""
    factory = request.app.state.db_factory
    if factory is None:
        raise HTTPException(status_code=503, detail="DB not configured")
    async with factory() as session:
        yield session


def get_admin_client(request: Request):
    """Достать GNS3AdminClient из SessionService (для прокси-эндпоинтов проектов)."""
    return request.app.state.session_service._admin
