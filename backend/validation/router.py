"""POST /labs/{slug}/sessions/{sid}/validate — SSE validation stream."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from config import settings
from db.session import get_db
from deps import get_gns3_client
from validation.service import (
    GNS3SessionMissing,
    LabSpecNotFound,
    SessionNotFound,
    prepare_validation,
    stream_validation,
)

router = APIRouter()


@router.post("/{slug}/sessions/{sid}/validate")
async def validate_lab(
    slug: str,
    sid: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
):
    """Start lab validation and stream check progress as SSE."""
    try:
        spec, gns3_sid = await prepare_validation(
            db=db, session_id=sid, lab_slug=slug, user_id=current_user["id"]
        )
    except SessionNotFound:
        raise HTTPException(status_code=404, detail="Session not found")
    except LabSpecNotFound:
        raise HTTPException(status_code=404, detail="Lab validation spec not found")
    except GNS3SessionMissing:
        raise HTTPException(status_code=400, detail="GNS3 session is not active")

    async def stream():
        """Convert validation events into SSE frames."""
        async for event in stream_validation(
            db=db,
            session_id=sid,
            lab_slug=slug,
            user_id=current_user["id"],
            spec=spec,
            gns3_sid=gns3_sid,
            settings=settings,
            gns3_client=gns3_client,
        ):
            yield event.to_sse()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
