"""Назначение экспериментальной группы."""

import random
from enum import Enum


class ExperimentGroup(str, Enum):
    """Группы эксперимента."""
    CONTROL = "control"
    EXPERIMENTAL = "experimental"


def assign_group() -> ExperimentGroup:
    """Случайное назначение группы 50/50."""
    return random.choice([ExperimentGroup.CONTROL, ExperimentGroup.EXPERIMENTAL])
