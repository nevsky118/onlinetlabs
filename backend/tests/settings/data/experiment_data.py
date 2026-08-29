# Test data generators for experiment.

from datetime import UTC, datetime, timedelta

from models.identity import User
from models.learning import LearningSession
from models.research import ExperimentMetrics


class ExperimentMetricsData:
    """Generates a duck-typed ExperimentMetrics."""

    def __init__(self, group: str, time: float, errors: int, repeated: int, interventions: int = 0):
        self.experiment_group = group
        self.total_time_seconds = time
        self.total_errors = errors
        self.repeated_errors = repeated
        self.interventions_received = interventions
        self.steps_completed = 5
        self.final_score = 100.0
        self.completed = True


class ExperimentMetricsRowData:
    """Generates a real ExperimentMetrics row for a finished session."""

    def __init__(
        self,
        user_id: str,
        session_id: str,
        *,
        lab_slug: str = "lan-static-ip",
        age_minutes: int = 10,
        seconds: float = 600.0,
        done: bool = True,
    ):
        self.row = ExperimentMetrics(
            id=f"m-{session_id}",
            session_id=session_id,
            user_id=user_id,
            lab_slug=lab_slug,
            experiment_group="closed",
            total_time_seconds=seconds,
            steps_completed=5,
            total_errors=0,
            repeated_errors=0,
            unique_error_types=0,
            final_score=100.0,
            completed=done,
            created_at=datetime.now(UTC) - timedelta(minutes=age_minutes),
        )


class ParticipantRosterData:
    """Generates an enrolled cohort plus one unenrolled user who must not appear.

    `prefix` keeps a second cohort from colliding with the first on primary keys.
    """

    def __init__(self, enrolled: int, prefix: str = "u", lab_slug: str = "lan-static-ip"):
        now = datetime.now(UTC)
        self.user_ids = [f"{prefix}-{i}" for i in range(enrolled)]
        self.outsider = User(
            id=f"outsider-{prefix}", email=f"out-{prefix}@test.local", role="student"
        )
        self.rows: list = [self.outsider]
        for user_id in self.user_ids:
            session_id = f"s-{user_id}"
            self.rows += [
                User(
                    id=user_id,
                    email=f"{user_id}@test.local",
                    role="student",
                    control_arm="closed",
                ),
                LearningSession(
                    id=session_id,
                    user_id=user_id,
                    lab_slug=lab_slug,
                    status="ended",
                    started_at=now,
                ),
                ExperimentMetricsRowData(user_id, session_id, lab_slug=lab_slug).row,
            ]


class UnfinishedParticipantData:
    """Generates an enrolled user who has no session and no metrics yet."""

    def __init__(self, user_id: str = "fresh", arm: str = "open"):
        self.user_id = user_id
        self.row = User(id=user_id, email=f"{user_id}@test.local", role="student", control_arm=arm)


class ExportMetricData:
    """Generates a duck-typed metrics row shaped for the CSV/JSON export."""

    def __init__(self, **overrides):
        defaults = {
            "user_id": "u1",
            "session_id": "s1",
            "experiment_group": "unknown",
            "agent_backend": None,
            "total_time_seconds": 120.0,
            "steps_completed": 4,
            "total_errors": 3,
            "repeated_errors": 2,
            "unique_error_types": 1,
            "interventions_received": 2,
            "interventions_succeeded": 1,
            "interventions_failed": 1,
            "final_score": 80.0,
            "completed": False,
        }
        for key, value in (defaults | overrides).items():
            setattr(self, key, value)
