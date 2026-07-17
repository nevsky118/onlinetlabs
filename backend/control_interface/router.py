"""Endpoints for managing the learner's consent."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from control_interface.consent import grant, list_active, revoke
from control_interface.schemas import (
    ConsentGrantRequest,
    ConsentItem,
    ConsentResponse,
    ConsentRevokeResponse,
)
from db.session import get_db

router = APIRouter()


@router.post("/consent", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def grant_consent(
    req: ConsentGrantRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grants or updates consent for the current user."""
    c = await grant(db, current_user["id"], req.scope, req.observe, req.act, req.data_policy)
    return ConsentResponse.model_validate(c)


@router.get("/consent", response_model=list[ConsentItem])
async def list_consent(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the current user's active consents."""
    return await list_active(db, current_user["id"])


@router.delete("/consent", response_model=ConsentRevokeResponse)
async def revoke_consent(
    scope: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revokes active consents for the given scope."""
    n = await revoke(db, current_user["id"], scope)
    return ConsentRevokeResponse(revoked=n)
