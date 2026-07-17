"""Admin data registry: table specs and row serialization for the admin panel."""

import datetime
import enum
import re
import uuid
from dataclasses import dataclass

from models.agent_activity_event import AgentActivityEventRow
from models.behavioral_event import BehavioralEvent
from models.chat_message import ChatMessage
from models.consent import Consent
from models.experiment import ExperimentMetrics
from models.mcp_audit import MCPAudit
from models.platform_event import PlatformEvent
from models.process_state_sample import ProcessStateSample
from models.progress import CourseProgress, LabProgress, StepAttempt
from models.session import LearningSession
from models.validation_run import ValidationRun

SECRET_RE = re.compile(r"(token|secret|key|jwt|password)", re.I)


@dataclass(frozen=True)
class TableSpec:
    model: type
    columns: list[str]
    sortable: set[str]
    searchable: list[str]
    masked: set[str]
    default_sort: str


ADMIN_TABLES: dict[str, TableSpec] = {
    "mcp_audit": TableSpec(
        model=MCPAudit,
        columns=[
            "id",
            "user_id",
            "session_id",
            "tool",
            "kind",
            "ts",
            "success",
            "error",
            "consent_ref",
            "lab_slug",
        ],
        sortable={"id", "ts", "user_id", "session_id", "kind", "tool"},
        searchable=["id", "user_id", "session_id", "tool", "kind", "lab_slug"],
        masked=set(),
        default_sort="ts",
    ),
    "agent_activity_events": TableSpec(
        model=AgentActivityEventRow,
        columns=[
            "id",
            "session_id",
            "user_id",
            "ts",
            "source",
            "kind",
            "agent",
            "severity",
            "summary",
        ],
        sortable={"id", "ts", "session_id", "user_id", "severity"},
        searchable=[
            "id",
            "session_id",
            "user_id",
            "source",
            "kind",
            "agent",
            "severity",
            "summary",
        ],
        masked=set(),
        default_sort="ts",
    ),
    "platform_events": TableSpec(
        model=PlatformEvent,
        columns=[
            "id",
            "event_name",
            "user_id",
            "session_id",
            "device_id",
            "properties",
            "client_ts",
            "server_ts",
        ],
        sortable={"id", "server_ts", "user_id", "session_id", "event_name"},
        searchable=["id", "event_name", "user_id", "session_id", "device_id"],
        masked=set(),
        default_sort="server_ts",
    ),
    "behavioral_events": TableSpec(
        model=BehavioralEvent,
        columns=[
            "id",
            "session_id",
            "user_id",
            "lab_slug",
            "timestamp",
            "event_type",
            "component_id",
            "component_type",
            "action",
            "raw_command",
            "success",
            "severity",
            "message",
        ],
        sortable={"id", "timestamp", "session_id", "user_id", "event_type"},
        searchable=[
            "id",
            "session_id",
            "user_id",
            "lab_slug",
            "event_type",
            "component_id",
            "component_type",
            "action",
            "raw_command",
            "severity",
            "message",
        ],
        masked=set(),
        default_sort="timestamp",
    ),
    "chat_messages": TableSpec(
        model=ChatMessage,
        columns=["id", "session_id", "role", "created_at"],
        sortable={"id", "created_at", "session_id", "role"},
        searchable=["id", "session_id", "role"],
        masked=set(),
        default_sort="created_at",
    ),
    "validation_runs": TableSpec(
        model=ValidationRun,
        columns=["id", "session_id", "lab_slug", "status", "started_at", "finished_at"],
        sortable={"id", "started_at", "session_id", "status"},
        searchable=["id", "session_id", "lab_slug", "status"],
        masked=set(),
        default_sort="started_at",
    ),
    "learning_sessions": TableSpec(
        model=LearningSession,
        columns=["id", "user_id", "lab_slug", "status", "started_at", "ended_at", "model_id"],
        sortable={"id", "started_at", "user_id", "status"},
        searchable=["id", "user_id", "lab_slug", "status", "model_id"],
        masked=set(),
        default_sort="started_at",
    ),
    "consents": TableSpec(
        model=Consent,
        columns=[
            "id",
            "user_id",
            "scope",
            "observe",
            "act",
            "granted_at",
            "revoked_at",
            "data_policy",
        ],
        sortable={"id", "granted_at", "user_id", "scope"},
        searchable=["id", "user_id", "scope", "data_policy"],
        masked=set(),
        default_sort="granted_at",
    ),
    "lab_progress": TableSpec(
        model=LabProgress,
        columns=[
            "id",
            "user_id",
            "lab_slug",
            "status",
            "score",
            "current_step",
            "started_at",
            "completed_at",
            "updated_at",
        ],
        sortable={"id", "updated_at", "user_id", "status"},
        searchable=["id", "user_id", "lab_slug", "status"],
        masked=set(),
        default_sort="updated_at",
    ),
    "course_progress": TableSpec(
        model=CourseProgress,
        columns=[
            "id",
            "user_id",
            "course_slug",
            "status",
            "score",
            "started_at",
            "completed_at",
            "updated_at",
        ],
        sortable={"id", "updated_at", "user_id", "status"},
        searchable=["id", "user_id", "course_slug", "status"],
        masked=set(),
        default_sort="updated_at",
    ),
    "step_attempts": TableSpec(
        model=StepAttempt,
        columns=[
            "id",
            "user_id",
            "lab_slug",
            "step_slug",
            "attempt_number",
            "result",
            "score",
            "started_at",
            "ended_at",
        ],
        sortable={"id", "started_at", "user_id", "result"},
        searchable=["id", "user_id", "lab_slug", "step_slug", "result"],
        masked=set(),
        default_sort="started_at",
    ),
    "process_state_samples": TableSpec(
        model=ProcessStateSample,
        columns=[
            "id",
            "session_id",
            "user_id",
            "lab_slug",
            "ts",
            "regime",
            "dwell_seconds",
            "created_at",
        ],
        sortable={"id", "ts", "session_id", "user_id"},
        searchable=["id", "session_id", "user_id", "lab_slug", "regime"],
        masked=set(),
        default_sort="ts",
    ),
    "experiment_metrics": TableSpec(
        model=ExperimentMetrics,
        columns=[
            "id",
            "session_id",
            "user_id",
            "lab_slug",
            "experiment_group",
            "agent_backend",
            "total_time_seconds",
            "steps_completed",
            "total_errors",
            "repeated_errors",
            "unique_error_types",
            "interventions_received",
            "interventions_succeeded",
            "interventions_failed",
            "interventions_accepted",
            "control_arm",
            "base_arm",
            "escalations",
            "would_interventions",
            "l1_interventions",
            "l2_unassisted_pass",
            "final_score",
            "completed",
            "completed_at",
            "created_at",
        ],
        sortable={"id", "created_at", "session_id", "user_id", "final_score"},
        searchable=[
            "id",
            "session_id",
            "user_id",
            "lab_slug",
            "experiment_group",
            "agent_backend",
            "control_arm",
            "base_arm",
        ],
        masked=set(),
        default_sort="created_at",
    ),
}


def serialize_row(spec: TableSpec, row: object) -> dict:
    result = {}
    for col in spec.columns:
        value = getattr(row, col)
        # mask
        if col in spec.masked or SECRET_RE.search(col):
            result[col] = "***"
            continue
        # JSON-normalize
        if isinstance(value, datetime.datetime):
            value = value.isoformat()
        elif isinstance(value, enum.Enum):
            value = value.value
        elif isinstance(value, uuid.UUID):
            value = str(value)
        # truncate
        if isinstance(value, (dict, list)):
            s = str(value)
            value = s[:200] + "…" if len(s) > 200 else s
        elif isinstance(value, str) and len(value) > 200:
            value = value[:200] + "…"
        result[col] = value
    return result
