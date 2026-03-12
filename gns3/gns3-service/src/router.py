# REST endpoints для gns3-service.

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from src.models import (
    ErrorResponse,
    HistoryEvent,
    PasswordResetResponse,
    ProjectCreate,
    ProjectResponse,
    SessionCreate,
    SessionResponse,
    SessionStatus,
)

router = APIRouter()


def _get_service(request: Request):
    return request.app.state.session_service


async def _get_db(request: Request):
    factory = request.app.state.db_factory
    if factory is None:
        raise HTTPException(status_code=503, detail="DB not configured")
    async with factory() as session:
        yield session


@router.post(
    "/sessions",
    status_code=201,
    response_model=SessionResponse,
    tags=["sessions"],
    summary="Создать лабораторную сессию",
    description=(
        "Клонирует шаблонный проект GNS3, создаёт изолированного пользователя "
        "и возвращает учётные данные для подключения. Пароль возвращается только один раз."
    ),
    responses={
        503: {"model": ErrorResponse, "description": "БД не сконфигурирована"},
    },
)
async def create_session(body: SessionCreate, service=Depends(_get_service), db=Depends(_get_db)):
    return await service.create_session(
        db=db,
        user_id=body.user_id,
        template_project_id=body.lab_template_project_id,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionStatus,
    tags=["sessions"],
    summary="Получить статус сессии",
    description="Возвращает текущее состояние лабораторной сессии по её UUID.",
    responses={
        404: {"model": ErrorResponse, "description": "Сессия не найдена"},
    },
)
async def get_session(
    session_id: str = Path(description="UUID сессии", examples=["f47ac10b-58cc-4372-a567-0e02b2c3d479"]),
    db=Depends(_get_db),
):
    from src.db.models import Session
    session = await db.get(Session, uuid.UUID(session_id))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionStatus(
        session_id=str(session.id),
        status=session.status.value,
        project_id=session.gns3_project_id,
        gns3_username=session.gns3_username,
        created_at=session.created_at,
    )


@router.post(
    "/sessions/{session_id}/reset-password",
    response_model=PasswordResetResponse,
    tags=["sessions"],
    summary="Сбросить пароль GNS3",
    description=(
        "Генерирует новый пароль для GNS3-пользователя сессии, "
        "обновляет его в GNS3 и возвращает новые учётные данные с JWT. "
        "Пароль возвращается один раз."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Сессия не найдена"},
        409: {"model": ErrorResponse, "description": "Сессия закрыта"},
    },
)
async def reset_password(
    session_id: str = Path(description="UUID сессии"),
    service=Depends(_get_service),
    db=Depends(_get_db),
):
    try:
        return await service.reset_password(db=db, session_id=session_id)
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=msg)
        if "closed" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise


@router.delete(
    "/sessions/{session_id}",
    tags=["sessions"],
    summary="Удалить сессию",
    description=(
        "Удаляет лабораторную сессию: останавливает проект GNS3, "
        "удаляет пользователя и очищает данные."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Сессия не найдена"},
    },
)
async def delete_session(
    session_id: str = Path(description="UUID сессии"),
    service=Depends(_get_service),
    db=Depends(_get_db),
):
    await service.delete_session(db=db, session_id=session_id)
    return {"status": "deleted"}


@router.get(
    "/history/{session_id}/actions",
    response_model=list[HistoryEvent],
    tags=["history"],
    summary="История действий сессии",
    description="Возвращает последние события из лабораторной сессии (узлы, линки, консоль и т.д.).",
    responses={
        404: {"model": ErrorResponse, "description": "Сессия не найдена"},
    },
)
async def get_history_actions(
    session_id: str = Path(description="UUID сессии"),
    limit: int = Query(default=50, ge=1, le=500, description="Макс. кол-во событий"),
    db=Depends(_get_db),
):
    from sqlalchemy import select
    from src.db.models import HistoryEvent as HistoryEventDB
    stmt = (
        select(HistoryEventDB)
        .where(HistoryEventDB.session_id == uuid.UUID(session_id))
        .order_by(HistoryEventDB.timestamp.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    events = result.scalars().all()
    return [
        HistoryEvent(
            timestamp=event.timestamp,
            event_type=event.event_type,
            component_id=event.component_id,
            data=event.data,
        )
        for event in events
    ]


@router.get("/health", tags=["health"], summary="Health check")
async def health(db=Depends(_get_db)):
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Projects (proxy to GNS3 server)
# ---------------------------------------------------------------------------


def _get_admin_client(request: Request):
    return request.app.state.session_service._admin


@router.post(
    "/projects",
    status_code=201,
    response_model=ProjectResponse,
    tags=["projects"],
    summary="Создать проект в GNS3",
)
async def create_project(body: ProjectCreate, request: Request):
    admin_client = _get_admin_client(request)
    result = await admin_client.create_project(body.name)
    return ProjectResponse(project_id=result["project_id"], name=result["name"])


@router.get(
    "/projects",
    response_model=list[ProjectResponse],
    tags=["projects"],
    summary="Список проектов GNS3",
)
async def list_projects(request: Request):
    admin_client = _get_admin_client(request)
    projects = await admin_client.list_projects()
    return [ProjectResponse(project_id=p["project_id"], name=p["name"]) for p in projects]


@router.delete(
    "/projects/{project_id}",
    status_code=204,
    tags=["projects"],
    summary="Удалить проект GNS3",
)
async def delete_project(project_id: str, request: Request):
    admin_client = _get_admin_client(request)
    await admin_client.delete_project(project_id)
