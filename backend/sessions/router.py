from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from db.session import get_db
from sessions.schemas import (
    LearningSessionCreate,
    LearningSessionResponse,
    LearningSessionUpdate,
)
from sessions.service import create_session, end_session, get_user_sessions

router = APIRouter()


@router.get("", response_model=list[LearningSessionResponse])
async def list_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sessions = await get_user_sessions(db, current_user["id"])
    return [
        LearningSessionResponse(
            id=s.id,
            lab_slug=s.lab_slug,
            status=s.status,
            started_at=s.started_at,
            ended_at=s.ended_at,
            meta=s.meta,
        )
        for s in sessions
    ]


@router.post("", response_model=LearningSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_endpoint(
    body: LearningSessionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await create_session(db, current_user["id"], body.lab_slug)
    return LearningSessionResponse(
        id=session.id,
        lab_slug=session.lab_slug,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        meta=session.meta,
    )


@router.patch("/{session_id}", response_model=LearningSessionResponse)
async def update_session_endpoint(
    session_id: str,
    body: LearningSessionUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await end_session(db, session_id, current_user["id"], body.status)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return LearningSessionResponse(
        id=session.id,
        lab_slug=session.lab_slug,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        meta=session.meta,
    )
