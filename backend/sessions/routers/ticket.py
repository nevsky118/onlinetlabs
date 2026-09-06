"""One-time GNS3 ticket redemption. The ticket is the credential, so no session cookie."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from i18n import LocalizedError
from kit.db import get_db
from kit.deps import get_gns3_client
from kit.rate_limit import limiter, ticket_rate_limit_key
from sessions.services.proxy import redeem_gns3_ticket

router = APIRouter(prefix="/gns3", tags=["gns3"])


async def _stash_redeem_ticket(request: Request) -> None:
    """Stashes the ticket into request.state before the rate limit check.

    ticket_rate_limit_key buckets by ticket, and slowapi computes the key before
    the handler body runs, so the value has to be on request.state by then.
    """
    try:
        body = await request.json()
        request.state.redeem_ticket = body.get("ticket")
    except Exception:
        request.state.redeem_ticket = None


class TicketRedeemRequest(BaseModel):
    """Body of POST /gns3/redeem."""

    ticket: str


class TicketRedeemResponse(BaseModel):
    """What the relay page needs to open the project without a password."""

    gns3_jwt: str
    project_id: str
    gns3_url: str


@router.post("/redeem", response_model=TicketRedeemResponse)
@limiter.limit("30/minute", key_func=ticket_rate_limit_key)
async def redeem(
    request: Request,
    body: TicketRedeemRequest,
    db: AsyncSession = Depends(get_db),
    gns3_client=Depends(get_gns3_client),
    _: None = Depends(_stash_redeem_ticket),
):
    """Exchanges a single-use ticket for a fresh GNS3 JWT."""
    result = await redeem_gns3_ticket(db, body.ticket, gns3_client)
    if result is None:
        raise LocalizedError("error.session.ticket_invalid", status_code=404)
    return TicketRedeemResponse(**result)
