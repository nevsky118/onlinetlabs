from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LearningSessionCreate(BaseModel):
    """Data for creating a learning session by lab slug."""

    lab_slug: str


class LearningSessionUpdate(BaseModel):
    """Learning session status change."""

    status: str


class SessionMeta(BaseModel):
    """GNS3 session metadata with encrypted password and JWT."""

    gns3_service_session_id: str
    gns3_user_id: str
    gns3_username: str
    gns3_project_id: str
    enc_password: str
    enc_jwt: str


class LearningSessionResponse(BaseModel):
    """Learning session in the API response."""

    id: str
    lab_slug: str
    lab_title: str | None = None
    status: str
    started_at: datetime
    ended_at: datetime | None
    meta: dict | None


class LaunchResponse(BaseModel):
    """Session launch response with GNS3 credentials and links."""

    session_id: str
    status: str
    gns3_username: str
    gns3_password: str
    gns3_url: str
    gns3_deep_url: str


class CredentialsResponse(BaseModel):
    """GNS3 credentials and links for the active session."""

    gns3_username: str
    gns3_password: str
    gns3_url: str
    gns3_deep_url: str


class NodeStateSchema(BaseModel):
    """State of a GNS3 topology node."""

    id: str
    name: str
    node_type: str = Field(alias="nodeType")
    status: Literal["started", "stopped", "suspended"]
    console: int | None
    console_type: str | None = Field(alias="consoleType")
    console_host: str = Field(alias="consoleHost")
    symbol: str

    model_config = {"populate_by_name": True}


class LinkEndpointSchema(BaseModel):
    """Link endpoint specifying node, adapter, and port."""

    node_id: str = Field(alias="nodeId")
    adapter_number: int = Field(alias="adapterNumber")
    port_number: int = Field(alias="portNumber")

    model_config = {"populate_by_name": True}


class LinkStateSchema(BaseModel):
    """Link between two topology node endpoints."""

    id: str
    nodes: list[LinkEndpointSchema]


class SessionMetricsSchema(BaseModel):
    """Summary metrics of the session topology."""

    nodes_total: int = Field(alias="nodesTotal")
    nodes_started: int = Field(alias="nodesStarted")
    links_count: int = Field(alias="linksCount")
    uptime_seconds: int = Field(alias="uptimeSeconds")

    model_config = {"populate_by_name": True}


class LabRef(BaseModel):
    """Short reference to a lab by slug and title."""

    slug: str
    title: str | None = None


class FullSessionStateResponse(BaseModel):
    """Full session state with nodes, links, and metrics."""

    session_id: str = Field(alias="sessionId")
    status: Literal["provisioning", "active", "ended", "error"]
    started_at: datetime = Field(alias="startedAt")
    lab: LabRef
    nodes: list[NodeStateSchema]
    links: list[LinkStateSchema]
    metrics: SessionMetricsSchema
    # L2 holdout: proactive hints suppressed (unassisted near-transfer)
    no_assist: bool = Field(default=False, alias="noAssist")

    model_config = {"populate_by_name": True}


class ActivityEventSchema(BaseModel):
    """Activity event within a session."""

    timestamp: datetime
    event_type: str = Field(alias="eventType")
    component_id: str | None = Field(alias="componentId")
    data: dict

    model_config = {"populate_by_name": True}


class ActivityResponseSchema(BaseModel):
    """Activity event feed with a cursor for pagination."""

    events: list[ActivityEventSchema]
    next_cursor: str | None = Field(alias="nextCursor")

    model_config = {"populate_by_name": True}


class ChatMessageResponse(BaseModel):
    """Session chat message in the API response."""

    id: str
    role: str
    parts: list
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
