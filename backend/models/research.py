"""Rows the study analyses. Never read back by the learner."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class BehavioralEvent(Base):
    """A behavioral event in a lab. Action on a component, command, and result."""

    __tablename__ = "behavioral_events"
    __table_args__ = (
        Index("ix_behavioral_events_session_ts", "session_id", "timestamp"),
        Index("ix_behavioral_events_user_lab", "user_id", "lab_slug"),
        Index("ix_behavioral_events_session_type", "session_id", "event_type"),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    lab_slug: Mapped[str] = mapped_column(String(255), ForeignKey("labs.slug", ondelete="CASCADE"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    component_id: Mapped[str | None] = mapped_column(String(255))
    component_type: Mapped[str | None] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(255))
    raw_command: Mapped[str | None] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean)
    severity: Mapped[str | None] = mapped_column(String(50))
    message: Mapped[str | None] = mapped_column(Text)
    extra_data: Mapped[dict | None] = mapped_column("metadata", JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class ProcessStateSample(Base):
    """A snapshot of the controlled process state (time series)."""

    __tablename__ = "process_state_samples"
    __table_args__ = (Index("ix_process_state_samples_session_ts", "session_id", "ts"),)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    lab_slug: Mapped[str] = mapped_column(String(255))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    regime: Mapped[str] = mapped_column(String(50))
    dwell_seconds: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class InterventionDecision(Base):
    """An MRT decision point: eligible moment + randomized assignment + spell outcome.

    Direct input to the hazard model (P4). An unconfounded intervene/withhold contrast
    over the dwell range is recovered by grouping on spell_id.
    """

    __tablename__ = "intervention_decisions"
    __table_args__ = (
        Index("ix_intervention_decisions_session_ts", "session_id", "ts"),
        Index("ix_intervention_decisions_spell", "spell_id"),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    lab_slug: Mapped[str] = mapped_column(String(255))
    spell_id: Mapped[str] = mapped_column(String(255))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    regime: Mapped[str] = mapped_column(String(50))
    dwell_seconds: Mapped[float] = mapped_column(Float)
    t_k_applied: Mapped[float] = mapped_column(Float)
    assignment: Mapped[str] = mapped_column(String(20))  # "intervene" | "withhold"
    subsequent_exit_ts: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    censored: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class RegimeAnnotation(Base):
    """A regime annotation by a coder for a session window (for IRR / kappa and adjudicated gold).

    coder_id is the annotator, NOT the rules author (else it's tautological). window_index
    aligns labels from different coders for Cohen's kappa. is_gold marks the adjudicated ground truth.
    """

    __tablename__ = "regime_annotations"
    __table_args__ = (Index("ix_regime_annotations_session_window", "session_id", "window_index"),)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    coder_id: Mapped[str] = mapped_column(String(255))
    window_index: Mapped[int] = mapped_column(Integer)
    regime_label: Mapped[str] = mapped_column(String(50))
    is_gold: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )


class GroundingComparison(Base):
    """A pair of help variants (with live MCP context vs. task text only).

    For blind expert evaluation: isolates the single novelty of "grounding in
    live environment state" with a metric that can't be computed from the rules.
    """

    __tablename__ = "grounding_comparisons"
    __table_args__ = (Index("ix_grounding_comparisons_session", "session_id"),)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    grounded_text: Mapped[str] = mapped_column(Text)
    ungrounded_text: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class CycleLatencySample(Base):
    """Latency of a single cycle stage (for p50/p95/p99 under load, not the mean)."""

    __tablename__ = "cycle_latency_samples"
    __table_args__ = (Index("ix_cycle_latency_samples_session_stage", "session_id", "stage"),)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    stage: Mapped[str] = mapped_column(String(50))  # analysis | mcp_context | llm | deliver
    duration_ms: Mapped[float] = mapped_column(Float)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class SessionEvidenceSnapshot(Base):
    """Raw session evidence for blind human annotation.

    A replayable stream (ordered by ts), DISJOINT from the 16 features and from the rules:
    the annotator codes the regime from raw material (MCP observations / topology / console),
    not from the feature vector, otherwise a tautological F1=1.0 results. kind is the evidence type.
    """

    __tablename__ = "session_evidence_snapshots"
    __table_args__ = (Index("ix_session_evidence_snapshots_session_ts", "session_id", "ts"),)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    lab_slug: Mapped[str] = mapped_column(String(255))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    kind: Mapped[str] = mapped_column(String(50))  # mcp_events | topology | console | ...
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class ExperimentMetrics(Base):
    """Final session metrics for statistical analysis."""

    __tablename__ = "experiment_metrics"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("learning_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    lab_slug: Mapped[str] = mapped_column(String(255))
    experiment_group: Mapped[str] = mapped_column(String(20))
    agent_backend: Mapped[str | None] = mapped_column(String(50), default=None)
    total_time_seconds: Mapped[float] = mapped_column(Float)
    steps_completed: Mapped[int] = mapped_column(Integer)
    total_errors: Mapped[int] = mapped_column(Integer)
    repeated_errors: Mapped[int] = mapped_column(Integer)
    unique_error_types: Mapped[int] = mapped_column(Integer)
    interventions_received: Mapped[int] = mapped_column(Integer, default=0)
    interventions_succeeded: Mapped[int] = mapped_column(Integer, default=0)
    interventions_failed: Mapped[int] = mapped_column(Integer, default=0)
    interventions_accepted: Mapped[int] = mapped_column(Integer, default=0)
    # Task 8: extended experiment metrics
    control_arm: Mapped[str | None] = mapped_column(String(20), default=None)
    # base_arm = the user's persistent training arm (User.control_arm); control_arm = the session's effective arm
    base_arm: Mapped[str | None] = mapped_column(String(20), default=None)
    escalations: Mapped[int] = mapped_column(Integer, default=0)
    would_interventions: Mapped[int] = mapped_column(Integer, default=0)
    l1_interventions: Mapped[int] = mapped_column(Integer, default=0)
    l2_unassisted_pass: Mapped[bool | None] = mapped_column(Boolean, default=None)
    final_score: Mapped[float] = mapped_column(Float)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
