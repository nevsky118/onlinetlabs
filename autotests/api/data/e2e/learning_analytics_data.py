# Test data generators for the Learning Analytics e2e tests.


class MCPContextTestData:
    """
    Test data for the e2e check of the MCP → AgentContext → LLM pipeline.

    :ivar project_name: GNS3 project name.
    :ivar user_question: Student question for the TutorAgent.
    :ivar struggle_type: Problem type for the AgentContext.
    :ivar dominant_error: Dominant error.
    """

    def __init__(self):
        self.project_name = "e2e-la-test"
        self.user_question = "Почему PC1 и PC2 не могут обмениваться данными?"
        self.struggle_type = "repeating_errors"
        self.dominant_error = "VLAN 10 not found"


class HintTestData:
    """
    Test data for checking the HintAgent.

    :ivar step_slug: The step where the student got stuck.
    :ivar last_error: Last error.
    :ivar attempts_count: Number of attempts, which determines hint_level.
    """

    def __init__(self, attempts_count: int = 4):
        self.step_slug = "step-1"
        self.last_error = "VLAN 10 not found on SW1"
        self.attempts_count = attempts_count


class ArmMetricData:
    """
    Metric row holding only the fields the arm analysis reads.

    :ivar experiment_group: Arm the session belongs to.
    :ivar total_time_seconds: Time the session took.
    :ivar repeated_errors: Number of repeated errors.
    """

    def __init__(self, group: str, time_s: float, repeated: int):
        self.experiment_group = group
        self.total_time_seconds = time_s
        self.repeated_errors = repeated


class RepeatedErrorEventsData:
    """
    A run of identical error events, which is what the identifier reads as a struggle.

    :ivar events: Behavioral events, all carrying the same error.
    """

    def __init__(self, count: int, session_id: str = "s1", user_id: str = "u1"):
        from datetime import datetime, timezone

        from models.behavioral_event import BehavioralEvent

        now = datetime.now(tz=timezone.utc)
        self.events = [
            BehavioralEvent(
                id=f"e{i}",
                session_id=session_id,
                user_id=user_id,
                lab_slug="autotest-lab",
                timestamp=now,
                event_type="error",
                action="cmd",
                success=False,
                message="same error",
                severity="error",
            )
            for i in range(count)
        ]
