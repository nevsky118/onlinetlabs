"""Pydantic schemas for the consent endpoints."""

from datetime import datetime

from pydantic import BaseModel


class ConsentGrantRequest(BaseModel):
    """Body of POST /users/me/consent."""

    scope: str  # study | product
    observe: bool
    act: bool
    data_policy: str | None = None


class ConsentResponse(BaseModel):
    """Response of POST /users/me/consent."""

    id: str
    user_id: str
    scope: str
    observe: bool
    act: bool
    granted_at: datetime
    revoked_at: datetime | None
    data_policy: str | None

    model_config = {"from_attributes": True}


class ConsentRevokeResponse(BaseModel):
    """Response of DELETE /users/me/consent."""

    revoked: int


class ConsentItem(BaseModel):
    """List item of GET /users/me/consent."""

    scope: str
    observe: bool
    act: bool
    granted_at: datetime
    model_config = {"from_attributes": True}
