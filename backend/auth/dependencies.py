from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import settings

security = HTTPBearer()

TOKEN_EXPIRE_MINUTES = 5


def create_backend_token(user_id: str, role: str) -> str:
    """Mint HS256 JWT with sub + role claims, 5min expiry."""
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.api.jwt_secret, algorithm="HS256")


def decode_backend_token(token: str, secret: str) -> dict:
    """Decode and verify HS256 JWT."""
    return jwt.decode(token, secret, algorithms=["HS256"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI dependency — extracts user from backend JWT."""
    try:
        payload = decode_backend_token(credentials.credentials, settings.api.jwt_secret)
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return {"id": user_id, "role": role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
