import logging
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from i18n import LocalizedError
from kit.db import get_db
from models.identity import User

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Short window. Token is refreshed by the frontend via /auth/exchange before every request.
TOKEN_EXPIRE_MINUTES = 5


def may_select_model(role: str, can_select_model: bool | None, selectable_roles: set[str]) -> bool:
    """Right to select a model: per-user toggle takes precedence, otherwise role default."""
    if can_select_model is not None:
        return can_select_model
    return role in selectable_roles


def may_view_agent_logs(
    role: str, can_view_agent_logs: bool | None, viewer_roles: set[str]
) -> bool:
    """Right to view agent logs: per-user toggle takes precedence, otherwise role default."""
    if can_view_agent_logs is not None:
        return can_view_agent_logs
    return role in viewer_roles


def can_view_session_activity(user: dict, session) -> bool:
    """Whether the user can see this session's activity."""
    if not user.get("can_view_logs"):
        return False
    return session.user_id == user["id"] or user.get("role") in ("instructor", "admin")


def create_backend_token(
    user_id: str,
    role: str,
    can_select: bool = False,
    can_view_logs: bool = False,
    is_active: bool = False,
) -> str:
    """Issues an HS256 JWT with claims sub, role, can_select, can_view_logs, is_active, 5-minute lifetime."""
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role,
        "can_select": can_select,
        "can_view_logs": can_view_logs,
        "is_active": is_active,
        "exp": now + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
        "iat": now,
    }
    return jwt.encode(payload, settings.api.jwt_secret, algorithm="HS256")


def decode_backend_token(token: str, secret: str) -> dict:
    """Decodes and verifies an HS256 JWT."""
    return jwt.decode(token, secret, algorithms=["HS256"])


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI dependency. Extracts the user from the backend JWT.

    Publishes the user on request.state for _rate_limit_key: slowapi computes the
    key before the handler body runs.
    """
    try:
        payload = decode_backend_token(credentials.credentials, settings.api.jwt_secret)
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = {
            "id": user_id,
            "role": role,
            "can_select": bool(payload.get("can_select")),
            "can_view_logs": bool(payload.get("can_view_logs")),
            "is_active": bool(payload.get("is_active")),
        }
        request.state.user = user
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> dict | None:
    """FastAPI dependency. Returns the user from the JWT or None without raising.

    Publishes the user on request.state for the rate limiter, as get_current_user does.
    """
    if credentials is None:
        return None
    try:
        payload = decode_backend_token(credentials.credentials, settings.api.jwt_secret)
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            return None
        user = {
            "id": user_id,
            "role": role,
            "can_select": bool(payload.get("can_select")),
            "can_view_logs": bool(payload.get("can_view_logs")),
            "is_active": bool(payload.get("is_active")),
        }
        request.state.user = user
        return user
    except jwt.InvalidTokenError:
        return None


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI dependency. Allows only the admin role."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


def require_instructor(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI dependency. Allows an instructor or admin.

    Used for the instructor dashboard: viewing student progress
    is available to the instructor and admin roles, but not student.
    """
    if current_user.get("role") not in ("instructor", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Instructor only")
    return current_user


async def require_active_user(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Allows only activated users. Otherwise 403.

    The claim is trusted while it says active. When it says inactive the row is
    reread, because the token outlives activation by its whole lifetime and a
    student the instructor just let in would otherwise keep being turned away.
    """
    if current_user.get("is_active"):
        return current_user
    user = await db.get(User, current_user["id"])
    if user is None or not user.is_active:
        raise LocalizedError("error.auth.inactive_account", status_code=403)
    return {**current_user, "is_active": True}


def require_internal_caller(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:
    """Authorizes server-to-server calls (Next.js to backend /auth/exchange).

    Compares Authorization Bearer INTERNAL_API_TOKEN against the shared secret. On
    mismatch returns 401, so a leaked client-side call can't obtain a
    backend JWT. The same token is used on the backend gns3-service channel.
    """
    expected = settings.security.internal_api_token
    if not expected or not secrets.compare_digest(credentials.credentials, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )


async def verify_jwt_for_ws(token: str | None) -> dict | None:
    """Verifies the JWT and returns the user or None on error. For WS handlers."""
    if not token:
        return None
    try:
        payload = decode_backend_token(token, settings.api.jwt_secret)
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            return None
        return {
            "id": user_id,
            "role": role,
            "can_select": bool(payload.get("can_select")),
            "can_view_logs": bool(payload.get("can_view_logs")),
            "is_active": bool(payload.get("is_active")),
        }
    except jwt.InvalidTokenError as exc:
        logger.warning("ws jwt verify failed", extra={"error": str(exc)})
        return None
