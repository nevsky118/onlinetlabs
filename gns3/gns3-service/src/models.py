# Pydantic schemas for the gns3-service API.

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Request to create a lab session."""

    user_id: str = Field(
        description="Platform user ID",
        examples=["user-42"],
    )
    lab_template_project_id: str = Field(
        description="UUID of the GNS3 template project to be cloned",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )


class SessionResponse(BaseModel):
    """Data of the created session. The password is returned only once."""

    session_id: str = Field(
        description="Session UUID",
        examples=["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
    )
    gns3_jwt: str = Field(
        description="JWT token for accessing the GNS3 API on behalf of the user",
    )
    project_id: str = Field(
        description="UUID of the cloned project in GNS3",
        examples=["b2c3d4e5-f6a7-8901-bcde-f12345678901"],
    )
    gns3_user_id: str = Field(
        description="User UUID in GNS3",
    )
    gns3_username: str = Field(
        description="Username in GNS3",
        examples=["student_user42"],
    )
    gns3_password: str = Field(
        description="Plaintext password, returned once. No longer stored in the DB.",
    )
    gns3_url: str = Field(
        description="GNS3 server URL for client connection",
        examples=["http://gns3.example.com:3080"],
    )
    gns3_deep_url: str = Field(
        description="Deep-link URL to open the student's project directly in the GNS3 Web UI",
        examples=["http://gns3.example.com:3080/static/web-ui/controller/1/project/<uuid>"],
    )


class HistoryEvent(BaseModel):
    """Event from the action history of a lab session."""

    timestamp: datetime = Field(
        description="Event time (UTC)",
    )
    event_type: str = Field(
        description="Event type",
        examples=["node.started", "link.created", "node.console"],
    )
    component_id: str | None = Field(
        default=None,
        description="UUID of the GNS3 component (node, link, etc.), if applicable",
    )
    data: dict = Field(
        description="Arbitrary event data",
        examples=[{"node_name": "R1", "status": "started"}],
    )


class ProjectResetResponse(BaseModel):
    """Data after resetting the session's project."""

    session_id: str = Field(
        description="Session UUID",
        examples=["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
    )
    project_id: str = Field(
        description="UUID of the newly cloned project in GNS3",
        examples=["c3d4e5f6-a7b8-9012-cdef-123456789012"],
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(
        description="Error description",
        examples=["Session not found"],
    )


class NodeState(BaseModel):
    """State of a GNS3 node in the session."""

    id: str = Field(description="GNS3 node UUID")
    name: str = Field(description="Node name visible to the student")
    node_type: str = Field(
        description="GNS3 node type (dynamips, qemu, ethernet_switch, vpcs, etc.)"
    )
    status: Literal["started", "stopped", "suspended"] = Field(description="Current node status")
    console: int | None = Field(description="Console TCP port (telnet/vnc/spice)")
    console_type: str | None = Field(description="Console type: telnet, vnc, spice")
    console_host: str = Field(description="Hostname for connecting to the console")
    symbol: str = Field(description="Path to the node's SVG symbol inside GNS3")


class LinkEndpoint(BaseModel):
    """One end of a link between nodes."""

    node_id: str = Field(description="UUID of the node at this end of the link")
    adapter_number: int = Field(description="Node network adapter number")
    port_number: int = Field(description="Port number within the adapter")


class LinkState(BaseModel):
    """Link between nodes in the GNS3 topology."""

    id: str = Field(description="GNS3 link UUID")
    nodes: list[LinkEndpoint] = Field(description="Link endpoints (usually two nodes)")


class SessionMetrics(BaseModel):
    """Aggregated session metrics for the UI."""

    nodes_total: int = Field(description="Total nodes in the project")
    nodes_started: int = Field(description="Nodes in started status")
    links_count: int = Field(description="Number of links")
    uptime_seconds: int = Field(description="Seconds elapsed since the session started")


class SessionStateResponse(BaseModel):
    """Full session state: nodes, links, metrics."""

    session_id: str = Field(description="Session UUID")
    project_id: str = Field(description="UUID of the session's GNS3 project")
    status: Literal["active", "closed"] = Field(description="Session status in gns3-service")
    started_at: datetime = Field(description="Session start time (UTC)")
    nodes: list[NodeState] = Field(description="List of nodes with their statuses")
    links: list[LinkState] = Field(description="List of links")
    metrics: SessionMetrics = Field(description="Aggregated metrics")
