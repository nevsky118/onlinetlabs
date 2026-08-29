"""HTTP surface for the tutor chat."""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_active_user
from chat.schemas import ChatModelsResponse, ChatStreamRequest
from chat.service import build_models_response, stream_reply
from i18n import Locale
from kit.db import get_db
from kit.deps import get_locale, get_mcp_client
from kit.rate_limit import limiter
from models.identity import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/models", response_model=ChatModelsResponse)
async def chat_models(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Models available for selection to the current user."""
    user = await db.get(User, current_user["id"])
    return build_models_response(
        current_user.get("can_select", False),
        user_default_model_id=user.default_model_id if user else None,
    )


@router.post("/stream")
@limiter.limit("30/minute")
async def chat_stream(
    body: ChatStreamRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    _active: dict = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
    mcp_client=Depends(get_mcp_client),
    locale: Locale = Depends(get_locale),
):
    """Streams the tutor's response for a session via SSE with tool-call support."""
    generator = await stream_reply(db, request, body, current_user, locale, mcp_client)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "x-vercel-ai-ui-message-stream": "v1",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
