from enum import Enum


class Difficulty(str, Enum):
    """Уровень сложности курса или лабы от начального до продвинутого."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ProgressStatus(str, Enum):
    """Статус прохождения курса или лабы. Не начато, в процессе, завершено."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class AttemptResult(str, Enum):
    """Итог попытки прохождения шага. Зачтено, провалено, частично."""

    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"


class SessionStatus(str, Enum):
    """Статус учебной сессии. Активна, завершена, заброшена."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class EnvironmentType(str, Enum):
    """Тип среды лабы. GNS3, Docker или без среды."""

    GNS3 = "gns3"
    DOCKER = "docker"
    NONE = "none"
