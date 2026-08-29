"""One-time GNS3 ticket redemption. The ticket is the credential, so no session cookie."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from i18n import LocalizedError
from kit.db import get_db
from kit.deps import get_gns3_client
from kit.rate_limit import limiter
from sessions.services.proxy import redeem_gns3_ticket

router = APIRouter(prefix="/gns3", tags=["gns3"])


class TicketRedeemRequest(BaseModel):
    """Body of POST /gns3/redeem."""

    ticket: str


class TicketRedeemResponse(BaseModel):
    """What the relay page needs to open the project without a password."""

    gns3_jwt: str
    project_id: str
    gns3_url: str


@router.post("/redeem", response_model=TicketRedeemResponse)
@limiter.limit("30/minute")
async def redeem(
    request: Request,
    body: TicketRedeemRequest,
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
):
    """Exchanges a single-use ticket for a fresh GNS3 JWT."""
    result = await redeem_gns3_ticket(db, body.ticket, gns3_client)
    if result is None:
        raise LocalizedError("error.session.ticket_invalid", status_code=404)
    return TicketRedeemResponse(**result)
