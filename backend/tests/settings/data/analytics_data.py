# Генераторы тестовых данных для analytics и learning_analytics.

from datetime import datetime, timedelta, timezone

from learning_analytics.context import AgentContext


class AttemptData:
    """Генерирует duck-typed StepAttempt."""

    def __init__(self, **overrides):
        now = datetime.now(tz=timezone.utc)
        defaults = {
            "id": "attempt-1",
            "step_slug": "step-1",
            "result": "pass",
            "attempt_number": 1,
            "score": 100.0,
            "started_at": now - timedelta(minutes=5),
            "ended_at": now,
            "error_details": None,
        }
        for key, value in (defaults | overrides).items():
            setattr(self, key, value)


class EventData:
    """Генерирует duck-typed BehavioralEvent."""

    def __init__(self, **overrides):
        now = datetime.now(tz=timezone.utc)
        defaults = {
            "id": "evt-1",
            "session_id": "sess-1",
            "user_id": "user-1",
            "lab_slug": "lab-1",
            "timestamp": now,
            "event_type": "action",
            "component_id": "node-1",
            "component_type": "qemu",
            "action": "start_node",
            "raw_command": None,
            "success": True,
            "severity": None,
            "message": None,
            "extra_data": None,
        }
        for key, value in (defaults | overrides).items():
            setattr(self, key, value)


class EventSequenceData:
    """Генерирует последовательность событий с заданным интервалом."""

    def __init__(self, count: int, interval_seconds: float = 10.0, **overrides):
        now = datetime.now(tz=timezone.utc)
        self.events = [
            EventData(
                id=f"evt-{i}",
                timestamp=now - timedelta(seconds=(count - i) * interval_seconds),
                **overrides,
            )
            for i in range(count)
        ]


class AgentContextData:
    """Генерирует AgentContext для тестов LLM-агентов."""

    def __init__(self, **overrides):
        defaults = dict(
            topology_summary="2 ноды (R1 running, R2 stopped)",
            recent_errors=["OSPF timeout"],
            recent_actions=["start_node(R1)"],
            struggle_type="repeating_errors",
            dominant_error="OSPF timeout",
            features_summary="10 событий",
        )
        self.context = AgentContext(**(defaults | overrides))


class SessionFeaturesData:
    """Генерирует дефолтные SessionFeatures kwargs."""

    def __init__(self, **overrides):
        defaults = dict(
            avg_inter_action_latency=10.0, action_rate_slope=0.0,
            idle_periods=0, total_active_time=300.0, time_on_current_step=20.0,
            error_repeat_count=0, error_repeat_rate=0.0,
            action_sequence_entropy=0.3, undo_redo_ratio=0.0,
            error_frequency=0.0, error_frequency_slope=0.0,
            unique_error_types=0, dominant_error=None,
            components_touched=5, action_diversity=0.5, events_total=30,
            session_id="s1", computed_at=datetime.now(tz=timezone.utc),
        )
        self.data = defaults | overrides
