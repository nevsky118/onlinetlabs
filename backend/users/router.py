"""Account endpoints: preferences, login sessions, subject data."""

from fastapi import APIRouter, Depends

from auth.dependencies import get_current_user
from kit.db import get_db
from users.data_export import collect_subject_data, erase_subject
from users.schemas import (
    ErasureResponse,
    PreferencesResponse,
    PreferencesUpdate,
    RevokeResponse,
    SessionsResponse,
)
from users.service import (
    get_preferences,
    list_login_sessions,
    revoke_all_login_sessions,
    revoke_login_session,
    set_default_model,
)

router = APIRouter(prefix="/users/me", tags=["users"])


@router.get("/preferences", response_model=PreferencesResponse)
async def read_preferences(current_user=Depends(get_current_user), db=Depends(get_db)):
    """The caller's account preferences."""
    user = await get_preferences(db, current_user["id"])
    return PreferencesResponse(default_model_id=user.default_model_id)


@router.patch("/preferences", response_model=PreferencesResponse)
async def update_preferences(
    body: PreferencesUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Updates only the fields the caller actually sent."""
    if "default_model_id" not in body.model_fields_set:
        user = await get_preferences(db, current_user["id"])
    else:
        user = await set_default_model(
            db,
            current_user["id"],
            body.default_model_id,
            can_select=current_user.get("can_select", False),
        )
    return PreferencesResponse(default_model_id=user.default_model_id)


# Login sessions. Path must stay distinct from /users/me/sessions, owned by sessions_router.
@router.get("/auth-sessions", response_model=SessionsResponse)
async def list_auth_sessions(current_user=Depends(get_current_user), db=Depends(get_db)):
    """Every login session the caller holds."""
    sessions = await list_login_sessions(db, current_user["id"])
    return SessionsResponse(sessions=sessions, count=len(sessions))


@router.delete("/auth-sessions/{session_id}", response_model=RevokeResponse)
async def revoke_auth_session(
    session_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Revokes one login session."""
    return RevokeResponse(revoked=await revoke_login_session(db, current_user["id"], session_id))


@router.delete("/auth-sessions", response_model=RevokeResponse)
async def revoke_all_auth_sessions(current_user=Depends(get_current_user), db=Depends(get_db)):
    """Revokes every login session the caller holds."""
    return RevokeResponse(revoked=await revoke_all_login_sessions(db, current_user["id"]))


@router.get("/data")
async def export_my_data(current_user=Depends(get_current_user), db=Depends(get_db)):
    """Everything the platform holds about the caller, table by table."""
    return await collect_subject_data(db, current_user["id"])


@router.delete("/data", response_model=ErasureResponse)
async def erase_my_data(current_user=Depends(get_current_user), db=Depends(get_db)):
    """Erases the caller's data and their account."""
    return ErasureResponse(removed=await erase_subject(db, current_user["id"]))
