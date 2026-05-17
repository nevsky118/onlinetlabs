# REST-эндпоинты истории действий и activity feed сессии.

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from src.models import ErrorResponse, HistoryEvent

from ._deps import get_db

router = APIRouter()


class ActivityResponse(BaseModel):
    events: list[HistoryEvent]
    next_cursor: str | None


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
    db=Depends(get_db),
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


@router.get(
    "/sessions/{session_id}/activity",
    response_model=ActivityResponse,
    tags=["history"],
    summary="История активности сессии (cursor-пагинация)",
    description=(
        "Возвращает события сессии в обратном хронологическом порядке. "
        "Используй next_cursor для подгрузки старых страниц. "
        "Максимум limit=200 за один запрос."
    ),
)
async def get_session_activity(
    session_id: str = Path(description="UUID сессии"),
    limit: int = Query(default=50, ge=1, le=200, description="Сколько событий вернуть (1-200)"),
    cursor: str | None = Query(default=None, description="ISO timestamp последнего события для пагинации"),
    db=Depends(get_db),
):
    from sqlalchemy import select
    from src.db.models import HistoryEvent as HistoryEventDB

    stmt = select(HistoryEventDB).where(
        HistoryEventDB.session_id == uuid.UUID(session_id),
    )
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor format; expected ISO 8601 timestamp")
        stmt = stmt.where(HistoryEventDB.timestamp < cursor_dt)
    stmt = stmt.order_by(HistoryEventDB.timestamp.desc()).limit(limit + 1)
    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    events = [
        HistoryEvent(
            timestamp=event.timestamp,
            event_type=event.event_type,
            component_id=event.component_id,
            data=event.data,
        )
        for event in rows
    ]
    next_cursor = rows[-1].timestamp.isoformat() if has_more and rows else None
    return ActivityResponse(events=events, next_cursor=next_cursor)
