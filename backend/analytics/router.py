from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.schemas import AnalyticsIngestRequest
from auth.dependencies import get_current_user_optional
from db.session import get_db
from models.platform_event import PlatformEvent
from rate_limit import limiter

router = APIRouter()


@router.post("/events", status_code=204)
@limiter.limit("120/minute")
async def ingest_events(
    request: Request,
    body: AnalyticsIngestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_current_user_optional),
):
    """Accepts a batch of platform telemetry events and saves them to the DB."""
    user_id = current_user["id"] if current_user else None
    request.state.user = current_user  # so the rate limiter can key by user_id
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
