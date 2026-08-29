"""Client telemetry ingest. Writes only for a consenting learner."""

import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from consent.consent import may_collect
from kit.db import get_db
from kit.rate_limit import limiter
from models.audit import PlatformEvent


class EventPayload(BaseModel):
    """A single platform telemetry event."""

    event_name: str = Field(max_length=100)
    properties: dict = Field(default_factory=dict)
    session_id: str | None = None
    client_ts: datetime

    @field_validator("properties")
    @classmethod
    def limit_properties_size(cls, v: dict) -> dict:
        """Checks that the properties size doesn't exceed 4 KB."""
        if len(json.dumps(v)) > 4096:
            raise ValueError("properties exceeds 4KB")
        return v


class AnalyticsIngestRequest(BaseModel):
    """Request to ingest a batch of telemetry events from a device."""

    device_id: str = Field(max_length=100)
    events: list[EventPayload] = Field(min_length=1, max_length=50)


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/events", status_code=204)
@limiter.limit("120/minute")
async def ingest_events(
    request: Request,
    body: AnalyticsIngestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Accepts a batch of platform telemetry events and saves them to the DB."""
    user_id = current_user["id"]
    if not await may_collect(db, user_id):
        return Response(status_code=204)
    now = datetime.now(UTC)

    for evt in body.events:
        db.add(
            PlatformEvent(
                event_name=evt.event_name,
                user_id=user_id,
                session_id=evt.session_id,
                device_id=body.device_id,
                properties=evt.properties,
                client_ts=evt.client_ts,
                server_ts=now,
            )
        )

    await db.commit()
    return Response(status_code=204)
