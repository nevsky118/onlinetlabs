"""Pydantic-схемы для эндпоинтов согласия."""

from datetime import datetime

from pydantic import BaseModel


class ConsentGrantRequest(BaseModel):
    """Тело POST /users/me/consent."""

    scope: str  # study | product
    observe: bool
    act: bool
    data_policy: str | None = None


class ConsentResponse(BaseModel):
    """Ответ POST /users/me/consent."""

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
    """Ответ DELETE /users/me/consent."""

    revoked: int


class ConsentItem(BaseModel):
    """Элемент списка GET /users/me/consent."""

    scope: str
    observe: bool
    act: bool
    granted_at: datetime
    model_config = {"from_attributes": True}
