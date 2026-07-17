from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request body for user registration by email and password."""

    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None


class LoginRequest(BaseModel):
    """Request body for login by email and password."""

    email: EmailStr
    password: str


class GitHubCallbackRequest(BaseModel):
    """GitHub profile data for login or account linking."""

    email: str
    name: str | None = None
    image: str | None = None
    provider_account_id: str


class ExchangeRequest(BaseModel):
    """Request body for exchanging a better-auth session for a backend JWT."""

    user_id: str
    email: str


class TokenResponse(BaseModel):
    """Response with the issued access token."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user data in the API response."""

    id: str
    email: str
    name: str | None
    image: str | None
    role: str


class ActivateRequest(BaseModel):
    """Request body for activating an account by email."""

    email: str
