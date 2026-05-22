from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import (
    create_backend_token,
    require_admin,
    require_internal_caller,
)
from rate_limit import limiter
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
    delete_user,
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
@limiter.limit("3/minute")
async def register(
    request: FastAPIRequest,
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Регистрирует нового пользователя. При занятом email возвращает 409."""
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
@limiter.limit("5/minute")
async def login(
    request: FastAPIRequest,
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Проверяет email и пароль. При неверных данных возвращает 401."""
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
@limiter.limit("30/minute")
async def exchange(
    request: FastAPIRequest,
    req: ExchangeRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_caller),
):
    """Обмен Better Auth сессии на backend-JWT.

    Вызывающая сторона обязана передать Authorization Bearer INTERNAL_API_TOKEN.
    Это подтверждает что запрос пришёл с Next.js сервера, который уже проверил
    better-auth сессию. Идентификатор пользователя это email из доверенного канала,
    backend выдаёт JWT на свой канонический User.id.
    """
    user = await get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    token = create_backend_token(user_id=user.id, role=user.role)
    return TokenResponse(access_token=token)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Удаляет пользователя по id (только для admin). При отсутствии возвращает 404."""
    deleted = await delete_user(db, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.post("/github-callback", response_model=UserResponse)
async def github_callback(
    req: GitHubCallbackRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_caller),
):
    """Создаёт или обновляет пользователя по данным GitHub и возвращает его профиль.

    Только server-to-server. Вызывающая сторона обязана передать Authorization
    Bearer INTERNAL_API_TOKEN, иначе любой браузер мог бы создавать пользователей.
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
