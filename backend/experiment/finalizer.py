"""Вычисление итоговых метрик эксперимента при завершении сессии."""

from datetime import datetime


def compute_session_metrics(
    events: list,
    started_at: datetime,
    ended_at: datetime,
    steps_completed: int,
    total_steps: int,
    experiment_group: str,
) -> dict:
    """События + мета сессии → dict метрик для ExperimentMetrics."""
    error_events = [e for e in events if e.event_type == "error"]
    intervention_events = [e for e in events if e.event_type == "intervention"]

    total_time = (ended_at - started_at).total_seconds()
    total_errors = len(error_events)
    repeated_errors = _max_consecutive_errors(error_events)
    unique_error_types = len({e.message for e in error_events if e.message})
    interventions_received = len(intervention_events)
    final_score = (steps_completed / total_steps * 100.0) if total_steps > 0 else 0.0

    return {
        "experiment_group": experiment_group,
        "total_time_seconds": total_time,
        "steps_completed": steps_completed,
        "total_errors": total_errors,
        "repeated_errors": repeated_errors,
        "unique_error_types": unique_error_types,
        "interventions_received": interventions_received,
        "interventions_accepted": 0,
        "final_score": round(final_score, 1),
        "completed": steps_completed >= total_steps,
        "completed_at": ended_at if steps_completed >= total_steps else None,
    }


def _max_consecutive_errors(error_events: list) -> int:
    """Макс. серия одинаковых ошибок подряд."""
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
