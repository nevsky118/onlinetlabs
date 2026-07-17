from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import (
    create_backend_token,
    may_select_model,
    may_view_agent_logs,
    require_admin,
    require_internal_caller,
)
from auth.schemas import (
    ActivateRequest,
    ExchangeRequest,
    GitHubCallbackRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from auth.service import (
    create_user,
    delete_user,
    get_user_by_email,
    hash_password_async,
    upsert_github_user,
    verify_password_async,
)
from config import settings
from db.session import get_db
from rate_limit import exchange_rate_limit_key, limiter

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(
    request: FastAPIRequest,
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Registers a new user. Returns 409 if the email is taken."""
    existing = await get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    password_hash = await hash_password_async(req.password)
    user = await create_user(
        db=db,
        email=req.email,
        password_hash=password_hash,
        name=req.name,
    )
    return UserResponse(
        id=user.id, email=user.email, name=user.name, image=user.image, role=user.role
    )


@router.post("/login", response_model=UserResponse)
@limiter.limit("5/minute")
async def login(
    request: FastAPIRequest,
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verifies email and password. Returns 401 on invalid credentials."""
    user = await get_user_by_email(db, req.email)
    if not user or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not await verify_password_async(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return UserResponse(
        id=user.id, email=user.email, name=user.name, image=user.image, role=user.role
    )


async def _stash_exchange_subject(request: FastAPIRequest) -> None:
    """Stashes the email from the body into request.state before the rate limit check.

    Reads the body via request.json() (Starlette caches it, so the repeat
    parse in ExchangeRequest reads from cache). We don't declare a body parameter,
    otherwise FastAPI would wrap two body fields into {req: {...}} and break the flat contract.
    Needed for the per-user rate limit key exchange_rate_limit_key.
    """
    try:
        body = await request.json()
        request.state.exchange_subject = body.get("email")
    except Exception:
        request.state.exchange_subject = None


@router.post("/exchange", response_model=TokenResponse)
@limiter.limit("60/minute", key_func=exchange_rate_limit_key)
async def exchange(
    request: FastAPIRequest,
    req: ExchangeRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_caller),
    __: None = Depends(_stash_exchange_subject),
):
    """Exchanges a Better Auth session for a backend JWT.

    The caller must pass Authorization Bearer INTERNAL_API_TOKEN.
    This confirms the request came from the Next.js server, which already verified
    the better-auth session. The user identifier is the email from a trusted channel,
    the backend issues a JWT against its canonical User.id.
    """
    user = await get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    can_select = may_select_model(
        user.role, user.can_select_model, settings.agents.selectable_roles
    )
    can_view_logs = may_view_agent_logs(
        user.role, user.can_view_agent_logs, settings.observability.viewer_roles
    )
    token = create_backend_token(
        user_id=user.id,
        role=user.role,
        can_select=can_select,
        can_view_logs=can_view_logs,
        is_active=user.is_active,
    )
    return TokenResponse(access_token=token)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Deletes a user by id (admin only). Returns 404 if not found."""
    deleted = await delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.post("/github-callback", response_model=UserResponse)
async def github_callback(
    req: GitHubCallbackRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_caller),
):
    """Creates or updates a user from GitHub data and returns their profile.

    Server-to-server only. The caller must pass Authorization
    Bearer INTERNAL_API_TOKEN, otherwise any browser could create users.
    """
    user = await upsert_github_user(
        db=db,
        email=req.email,
        name=req.name,
        image=req.image,
        provider_account_id=req.provider_account_id,
    )
    return UserResponse(
        id=user.id, email=user.email, name=user.name, image=user.image, role=user.role
    )


@router.post("/activate", status_code=200)
async def activate(
    req: ActivateRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_caller),
):
    """Activates a user's account by email. Server-to-server only."""
    user = await get_user_by_email(db, req.email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    await db.commit()
    return {"email": req.email, "is_active": True}
