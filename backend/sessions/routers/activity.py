from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from db.session import get_db
from deps import get_gns3_client
from sessions.schemas import ActivityResponseSchema
from sessions.service import proxy_activity

router = APIRouter()


@router.get("/{session_id}/activity", response_model=ActivityResponseSchema)
async def get_activity_endpoint(
    session_id: str,
    limit: int = 50,
    cursor: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
):
    """Возвращает ленту активности сессии с постраничной навигацией по курсору."""
    result = await proxy_activity(
        db,
        session_id,
        current_user["id"],
        limit,
        cursor,
        gns3_client,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return result
