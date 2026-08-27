# REST endpoints for lab sessions: CRUD and node operations.

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from src.models import (
    ErrorResponse,
    ProjectResetResponse,
    SessionCreate,
    SessionResponse,
    SessionStateResponse,
)

from ._deps import get_db, get_service

router = APIRouter()


@router.post(
    "/sessions",
    status_code=201,
    response_model=SessionResponse,
    tags=["sessions"],
    summary="Create a lab session",
    description=(
        "Clones the GNS3 template project, creates an isolated user "
        "and returns the connection credentials. The password is returned only once."
    ),
    responses={
        503: {"model": ErrorResponse, "description": "Database is not configured"},
    },
)
async def create_session(body: SessionCreate, service=Depends(get_service), db=Depends(get_db)):
    return await service.create_session(
        db=db,
        user_id=body.user_id,
        template_project_id=body.lab_template_project_id,
    )


@router.get(
    "/sessions/{session_id}/state",
    response_model=SessionStateResponse,
    tags=["sessions"],
    summary="Get session state",
    description=(
        "Returns the current state of the session GNS3 project: nodes, links, metrics. "
        "Cached in-memory for 5 seconds."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        502: {"model": ErrorResponse, "description": "GNS3 is unavailable"},
    },
)
async def get_session_state(
    session_id: str = Path(description="Session UUID"),
    service=Depends(get_service),
    db=Depends(get_db),
):
    # SessionNotFound propagates and is caught by the global handler → 404.
    # Any other error means GNS3 is unreachable → 502.
    try:
        return await service.get_state(db=db, session_id=session_id)
    except ValueError:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="GNS3 unreachable")


class ProjectResetRequest(BaseModel):
    lab_template_project_id: str = Field(
        description="UUID of the GNS3 template project to clone again",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )


@router.post(
    "/sessions/{session_id}/reset-project",
    response_model=ProjectResetResponse,
    tags=["sessions"],
    summary="Reset the session project",
    description=(
        "Deletes the current cloned GNS3 project and creates a new one from the template. "
        "The ACL for the session GNS3 user is set on the new project automatically."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        409: {"model": ErrorResponse, "description": "Session closed"},
    },
)
async def reset_project(
    session_id: str = Path(description="Session UUID"),
    body: ProjectResetRequest = ...,
    service=Depends(get_service),
    db=Depends(get_db),
):
    return await service.reset_project(
        db=db,
        session_id=session_id,
        template_project_id=body.lab_template_project_id,
    )


@router.delete(
    "/sessions/{session_id}",
    tags=["sessions"],
    summary="Delete the session",
    description=(
        "Deletes the lab session: stops the GNS3 project, removes the user and clears the data."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def delete_session(
    session_id: str = Path(description="Session UUID"),
    service=Depends(get_service),
    db=Depends(get_db),
):
    await service.delete_session(db=db, session_id=session_id)
    return {"status": "deleted"}


NodeAction = Literal["start", "stop", "suspend", "reload"]


@router.post(
    "/sessions/{session_id}/nodes/{node_id}/{action}",
    status_code=204,
    tags=["sessions"],
    summary="Control a session node",
    description="Starts, stops, suspends or reloads a single GNS3 node.",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        409: {"model": ErrorResponse, "description": "Session closed"},
    },
)
async def post_node_action(
    session_id: str = Path(description="Session UUID"),
    node_id: str = Path(description="Node UUID"),
    action: NodeAction = Path(description="Node action"),
    service=Depends(get_service),
    db=Depends(get_db),
):
    await service.node_action(db=db, session_id=session_id, node_id=node_id, action=action)


@router.post(
    "/sessions/{session_id}/nodes/{action}",
    status_code=204,
    tags=["sessions"],
    summary="Bulk action on all session nodes",
    description="Applies an action (start/stop/suspend/reload) to all project nodes at once.",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        409: {"model": ErrorResponse, "description": "Session closed"},
    },
)
async def post_bulk_node_action(
    session_id: str = Path(description="Session UUID"),
    action: NodeAction = Path(description="Action for all nodes"),
    service=Depends(get_service),
    db=Depends(get_db),
):
    await service.bulk_node_action(db=db, session_id=session_id, action=action)
