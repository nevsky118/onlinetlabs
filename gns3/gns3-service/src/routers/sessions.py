# REST-эндпоинты лабораторных сессий: CRUD и операции над узлами.

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from src.models import (
    ErrorResponse,
    PasswordResetResponse,
    ProjectResetResponse,
    SessionCreate,
    SessionResponse,
    SessionStateResponse,
    SessionStatus,
)

from ._deps import get_db, get_service

router = APIRouter()


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
async def create_session(body: SessionCreate, service=Depends(get_service), db=Depends(get_db)):
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
    session_id: str = Path(
        description="UUID сессии", examples=["f47ac10b-58cc-4372-a567-0e02b2c3d479"]
    ),
    db=Depends(get_db),
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


@router.get(
    "/sessions/{session_id}/state",
    response_model=SessionStateResponse,
    tags=["sessions"],
    summary="Получить состояние сессии",
    description=(
        "Возвращает текущее состояние GNS3-проекта сессии: узлы, links, метрики. "
        "Кешируется на 5 секунд in-memory."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Сессия не найдена"},
        502: {"model": ErrorResponse, "description": "GNS3 недоступен"},
    },
)
async def get_session_state(
    session_id: str = Path(description="UUID сессии"),
    service=Depends(get_service),
    db=Depends(get_db),
):
    # SessionNotFound пробрасывается и ловится глобальным handler'ом → 404.
    # Любая иная ошибка означает недоступность GNS3 → 502.
    try:
        return await service.get_state(db=db, session_id=session_id)
    except ValueError:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="GNS3 unreachable")


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
    service=Depends(get_service),
    db=Depends(get_db),
):
    return await service.reset_password(db=db, session_id=session_id)


class ProjectResetRequest(BaseModel):
    lab_template_project_id: str = Field(
        description="UUID шаблонного проекта GNS3 для повторного клонирования",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )


@router.post(
    "/sessions/{session_id}/reset-project",
    response_model=ProjectResetResponse,
    tags=["sessions"],
    summary="Сбросить проект сессии",
    description=(
        "Удаляет текущий клонированный проект GNS3 и создаёт новый из шаблона. "
        "ACL для GNS3-пользователя сессии выставляется на новый проект автоматически."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Сессия не найдена"},
        409: {"model": ErrorResponse, "description": "Сессия закрыта"},
    },
)
async def reset_project(
    session_id: str = Path(description="UUID сессии"),
    body: ProjectResetRequest = ...,
    service=Depends(get_service),
    db=Depends(get_db),
):
    return await service.reset_project(
        db=db,
        session_id=session_id,
        template_project_id=body.lab_template_project_id,
    )


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
    service=Depends(get_service),
    db=Depends(get_db),
):
    await service.delete_session(db=db, session_id=session_id)
    return {"status": "deleted"}


NodeAction = Literal["start", "stop", "suspend", "reload"]


@router.post(
    "/sessions/{session_id}/nodes/{node_id}/{action}",
    status_code=204,
    tags=["sessions"],
    summary="Управление узлом сессии",
    description="Запускает, останавливает, приостанавливает или перезагружает один узел GNS3.",
    responses={
        404: {"model": ErrorResponse, "description": "Сессия не найдена"},
        409: {"model": ErrorResponse, "description": "Сессия закрыта"},
    },
)
async def post_node_action(
    session_id: str = Path(description="UUID сессии"),
    node_id: str = Path(description="UUID узла"),
    action: NodeAction = Path(description="Действие над узлом"),
    service=Depends(get_service),
    db=Depends(get_db),
):
    await service.node_action(db=db, session_id=session_id, node_id=node_id, action=action)


@router.post(
    "/sessions/{session_id}/nodes/{action}",
    status_code=204,
    tags=["sessions"],
    summary="Bulk-действие над всеми узлами сессии",
    description="Применяет действие (start/stop/suspend/reload) ко всем узлам проекта одной операцией.",
    responses={
        404: {"model": ErrorResponse, "description": "Сессия не найдена"},
        409: {"model": ErrorResponse, "description": "Сессия закрыта"},
    },
)
async def post_bulk_node_action(
    session_id: str = Path(description="UUID сессии"),
    action: NodeAction = Path(description="Действие над всеми узлами"),
    service=Depends(get_service),
    db=Depends(get_db),
):
    await service.bulk_node_action(db=db, session_id=session_id, action=action)
