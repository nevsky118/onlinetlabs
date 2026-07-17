"""Computing final experiment metrics when a session ends."""

from datetime import datetime


def compute_session_metrics(
    events: list,
    started_at: datetime,
    ended_at: datetime,
    steps_completed: int,
    total_steps: int,
    experiment_group: str,
    agent_backend: str | None = None,
    control_arm: str | None = None,
    base_arm: str | None = None,
    l2_intervention_cap: int = 0,
    is_l2: bool = False,
) -> dict:
    """Events + session metadata -> a metrics dict for ExperimentMetrics.

    is_l2: True if the calling code determined this is an L2-holdout session.
    Only then is l2_unassisted_pass computed; otherwise None.
    """
    error_events = [e for e in events if e.event_type == "error"]
    intervention_events = [e for e in events if e.event_type == "intervention"]
    successful_interventions = [e for e in intervention_events if e.success]

    total_time = (ended_at - started_at).total_seconds()
    total_errors = len(error_events)
    repeated_errors = _max_consecutive_errors(error_events)
    unique_error_types = len({e.message for e in error_events if e.message})
    interventions_received = len(intervention_events)
    interventions_succeeded = len(successful_interventions)
    interventions_failed = interventions_received - interventions_succeeded
    final_score = (steps_completed / total_steps * 100.0) if total_steps > 0 else 0.0
    completed = steps_completed >= total_steps

    # Task 8: new metrics
    escalations = len([e for e in events if e.event_type == "escalation"])
    would_interventions = len([e for e in events if e.event_type == "would_intervene"])
    l2_unassisted_pass: bool | None = None
    if is_l2:
        l2_unassisted_pass = completed and interventions_received <= l2_intervention_cap

    return {
        "experiment_group": experiment_group,
        "agent_backend": agent_backend,
        "total_time_seconds": total_time,
        "steps_completed": steps_completed,
        "total_errors": total_errors,
        "repeated_errors": repeated_errors,
        "unique_error_types": unique_error_types,
        "interventions_received": interventions_received,
        "interventions_succeeded": interventions_succeeded,
        "interventions_failed": interventions_failed,
        "interventions_accepted": 0,
        "final_score": round(final_score, 1),
        "completed": completed,
        "completed_at": ended_at if completed else None,
        # Task 8
        "control_arm": control_arm,
        "base_arm": base_arm,
        "escalations": escalations,
        "would_interventions": would_interventions,
        "l1_interventions": interventions_received,
        "l2_unassisted_pass": l2_unassisted_pass,
    }


def _max_consecutive_errors(error_events: list) -> int:
    """Longest run of consecutive identical errors."""
    best = 0
    run = 1
    prev = None
    for event in error_events:
        if event.message == prev and prev is not None:
            run += 1
            best = max(best, run)
        else:
            run = 1
        prev = event.message
    return best
