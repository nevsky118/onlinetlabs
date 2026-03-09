from enum import Enum


class Difficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ProgressStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class AttemptResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class EnvironmentType(str, Enum):
    GNS3 = "gns3"
    DOCKER = "docker"
    NONE = "none"
