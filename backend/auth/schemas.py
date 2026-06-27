from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Тело запроса на регистрацию пользователя по email и паролю."""

    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None


class LoginRequest(BaseModel):
    """Тело запроса на вход по email и паролю."""

    email: EmailStr
    password: str


class GitHubCallbackRequest(BaseModel):
    """Данные профиля GitHub для входа или привязки аккаунта."""

    email: str
    name: str | None = None
    image: str | None = None
    provider_account_id: str


class ExchangeRequest(BaseModel):
    """Тело запроса на обмен better-auth сессии на backend-JWT."""

    user_id: str
    email: str


class TokenResponse(BaseModel):
    """Ответ с выданным access-токеном."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Публичные данные пользователя в ответе API."""

    id: str
    email: str
    name: str | None
    image: str | None
    role: str


class ActivateRequest(BaseModel):
    """Тело запроса на активацию аккаунта по email."""

    email: str
