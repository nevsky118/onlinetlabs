"""Эндпоинты управления согласием обучаемого."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from control_interface.consent import grant, revoke
from control_interface.schemas import ConsentGrantRequest, ConsentResponse, ConsentRevokeResponse
from db.session import get_db

router = APIRouter()


@router.post("/consent", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def grant_consent(
    req: ConsentGrantRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Выдаёт или обновляет согласие текущего пользователя."""
    c = await grant(db, current_user["id"], req.scope, req.observe, req.act, req.data_policy)
    return ConsentResponse.model_validate(c)


@router.delete("/consent", response_model=ConsentRevokeResponse)
async def revoke_consent(
    scope: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отзывает активные согласия указанного scope."""
    n = await revoke(db, current_user["id"], scope)
    return ConsentRevokeResponse(revoked=n)
