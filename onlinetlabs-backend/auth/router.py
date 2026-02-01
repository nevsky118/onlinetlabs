from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import create_backend_token
from auth.schemas import (
    ExchangeRequest,
    GitHubCallbackRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from auth.service import (
    create_user,
    get_user_by_email,
    hash_password_async,
    upsert_github_user,
    verify_password,
)
from db.session import get_db

router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

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
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, req.email)
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    return UserResponse(
        id=user.id, email=user.email, name=user.name, image=user.image, role=user.role
    )


@router.post("/exchange", response_model=TokenResponse)
async def exchange(req: ExchangeRequest, db: AsyncSession = Depends(get_db)):
    """Exchange Better Auth session data for a backend JWT."""
    user = await get_user_by_email(db, req.email)
    if not user or user.id != req.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    token = create_backend_token(user_id=user.id, role=user.role)
    return TokenResponse(access_token=token)


@router.post("/github-callback", response_model=UserResponse)
async def github_callback(
    req: GitHubCallbackRequest, db: AsyncSession = Depends(get_db)
):
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
