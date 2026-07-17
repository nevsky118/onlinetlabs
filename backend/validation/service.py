"""Validation service layer — owner-guard, running the runner, recording the result."""

from collections.abc import AsyncIterator
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from gns3_service_client import Gns3ServiceClient
from progress.service import record_lab_validation
from sessions.services.query import get_owned_session
from validation.checks.registry import CheckContext
from validation.repository import create_run, finish_run
from validation.runner import load_lab_spec, run_validation
from validation.stream import Event


class ValidationError(Exception):
    """Base lab validation error."""

    pass


class SessionNotFound(ValidationError):
    """Session not found or doesn't belong to the user."""

    pass


class LabSpecNotFound(ValidationError):
    """No YAML checks spec exists for the lab."""

    pass


class GNS3SessionMissing(ValidationError):
    """The session has no active GNS3 session to run checks against."""

    pass


def _gns3_host_from_settings(settings) -> str:
    """Determine the GNS3 host for outbound connections from settings."""
    gns3 = getattr(settings, "gns3", None)
    if gns3 is not None:
        node_host = getattr(gns3, "node_host", "") or ""
        if node_host:
            return node_host
        for attr in ("internal_url", "public_url"):
            url = getattr(gns3, attr, "") or ""
            if url:
                host = urlparse(url).hostname or ""
                if host and host not in ("gns3-server",):
                    return host
    raise ValueError("cannot derive GNS3 node host from settings")


async def prepare_validation(
    db: AsyncSession,
    session_id: str,
    lab_slug: str,
    user_id: str,
) -> tuple[dict, str]:
    """Pre-flight: owner-guard + loading the YAML + checking the gns3 session.

    Returns: `(spec, gns3_service_session_id)`.
    Raises: SessionNotFound, LabSpecNotFound, GNS3SessionMissing.
    """
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        raise SessionNotFound(session_id)

    spec = load_lab_spec(lab_slug)
    if spec is None:
        raise LabSpecNotFound(lab_slug)

    gns3_sid = (session.meta or {}).get("gns3_service_session_id")
    if not gns3_sid:
        raise GNS3SessionMissing(session_id)

    return spec, gns3_sid


async def build_check_context(gns3_client, gns3_sid: str, settings) -> CheckContext:
    """GNS3 session state -> CheckContext for running checks."""
    state = await gns3_client.get_state(gns3_sid)
    nodes = state.get("nodes") or []
    nodes_by_name = {n.get("name"): n for n in nodes if n.get("name")}
    return CheckContext(
        gns3_host=_gns3_host_from_settings(settings),
        nodes_by_name=nodes_by_name,
        gns3_project_id=state.get("project_id", ""),
        frr_client=gns3_client,
    )


async def stream_validation(
    db: AsyncSession,
    session_id: str,
    lab_slug: str,
    user_id: str,
    spec: dict,
    gns3_sid: str,
    settings,
    gns3_client: Gns3ServiceClient,
) -> AsyncIterator[Event]:
    """Drives the runner and writes the final result to the DB."""
    ctx = await build_check_context(gns3_client, gns3_sid, settings)

    run_id = await create_run(db, session_id, lab_slug)

    final_status = "failed"
    final_steps: list = []
    try:
        async for event, steps_snapshot in run_validation(ctx, spec):
            if event.type == "run.start":
                event.data["runId"] = run_id
            elif event.type == "run.finish":
                event.data["runId"] = run_id
                final_status = "passed" if event.data.get("ok") else "failed"
                final_steps = list(steps_snapshot)
            yield event
    finally:
        await finish_run(db, run_id, final_status, final_steps)
        # The validation run is the only signal of lab progress: carry
        # its outcome into LabProgress (score + status), which is what the
        # student and the instructor dashboard read from.
        if final_steps:
            await record_lab_validation(db, user_id, lab_slug, final_steps)
