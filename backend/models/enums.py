from enum import Enum


class Difficulty(str, Enum):
    """Difficulty level of a course or lab, from beginner to advanced."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ProgressStatus(str, Enum):
    """Progress status of a course or lab. Not started, in progress, completed."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class AttemptResult(str, Enum):
    """Outcome of a step attempt. Passed, failed, partial."""

    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"


class SessionStatus(str, Enum):
    """Learning session status. Active, completed, abandoned."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class EnvironmentType(str, Enum):
    """Lab environment type. GNS3, Docker, or none."""

    GNS3 = "gns3"
    DOCKER = "docker"
    NONE = "none"
