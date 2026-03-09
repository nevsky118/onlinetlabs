from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GitHubCallbackRequest(BaseModel):
    email: str
    name: str | None = None
    image: str | None = None
    provider_account_id: str


class ExchangeRequest(BaseModel):
    user_id: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    image: str | None
    role: str
