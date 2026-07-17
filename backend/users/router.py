from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select

from auth.dependencies import get_current_user
from config import settings
from db.session import get_db
from models.user import Session, User

router = APIRouter()


class PreferencesResponse(BaseModel):
    default_model_id: str | None


class PreferencesUpdate(BaseModel):
    default_model_id: str | None = None


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(current_user=Depends(get_current_user), db=Depends(get_db)):
    user = await db.get(User, current_user["id"])
    if user is None:
        raise HTTPException(404, "Пользователь не найден")
    return PreferencesResponse(default_model_id=user.default_model_id)


@router.patch("/preferences", response_model=PreferencesResponse)
async def update_preferences(
    body: PreferencesUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    user = await db.get(User, current_user["id"])
    if user is None:
        raise HTTPException(404, "Пользователь не найден")
    if "default_model_id" in body.model_fields_set:
        val = body.default_model_id
        if val is not None:
            if not current_user.get("can_select", False):
                raise HTTPException(403, "Выбор модели недоступен")
            if settings.agents.get_entry(val) is None:
                raise HTTPException(422, "Неизвестная модель")
            user.default_model_id = val
        else:
            user.default_model_id = None  # очистка
        await db.commit()
        await db.refresh(user)
    return PreferencesResponse(default_model_id=user.default_model_id)


class SessionItem(BaseModel):
    id: str
    expires: datetime
    current: bool = False
    model_config = {"from_attributes": True}


class SessionsResponse(BaseModel):
    sessions: list[SessionItem]
    count: int


class RevokeResponse(BaseModel):
    revoked: int


@router.get("/sessions", response_model=SessionsResponse)
async def list_sessions(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user["id"])
        .order_by(Session.expires.desc())
    )
    sessions = result.scalars().all()
    return SessionsResponse(sessions=sessions, count=len(sessions))


@router.delete("/sessions/{session_id}", response_model=RevokeResponse)
async def revoke_session(
    session_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user["id"],
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return RevokeResponse(revoked=1)


@router.delete("/sessions", response_model=RevokeResponse)
async def revoke_all_sessions(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await db.execute(delete(Session).where(Session.user_id == current_user["id"]))
    await db.commit()
    return RevokeResponse(revoked=result.rowcount)
