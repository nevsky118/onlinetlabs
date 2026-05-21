from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from db.session import get_db
from sessions.schemas import CredentialsResponse
from sessions.service import get_credentials

router = APIRouter()


@router.get("/{session_id}/credentials", response_model=CredentialsResponse)
async def credentials_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает учётные данные доступа к GNS3 для сессии."""
    creds = await get_credentials(db, session_id, current_user["id"])
    if creds is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return CredentialsResponse(**creds)
