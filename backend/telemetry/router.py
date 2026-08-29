from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from control_interface.consent import may_collect
from db.session import get_db
from models.platform_event import PlatformEvent
from rate_limit import limiter
from telemetry.schemas import AnalyticsIngestRequest

router = APIRouter()


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
