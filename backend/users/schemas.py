"""Pydantic schemas for the account API."""

from datetime import datetime

from pydantic import BaseModel


class PreferencesResponse(BaseModel):
    """The caller's account preferences."""

    default_model_id: str | None


class PreferencesUpdate(BaseModel):
    """Patch body; an unset field is left alone, an explicit null clears it."""

    default_model_id: str | None = None


class SessionItem(BaseModel):
    """One login session."""

    id: str
    expires: datetime
    current: bool = False
    model_config = {"from_attributes": True}


class SessionsResponse(BaseModel):
    """Every login session the caller holds."""

    sessions: list[SessionItem]
    count: int


class RevokeResponse(BaseModel):
    """How many login sessions were revoked."""

    revoked: int


class ErasureResponse(BaseModel):
    """How many rows the erasure removed, table by table."""

    removed: dict[str, int]
