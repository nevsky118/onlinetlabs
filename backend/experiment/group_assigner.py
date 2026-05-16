"""Назначение экспериментальной группы."""

import random
from enum import Enum


class ExperimentGroup(str, Enum):
    """Группы эксперимента."""

    GROUP_A = "group_a"
    GROUP_B = "group_b"


class AgentBackend(str, Enum):
    """Бэкенд, соответствующий экспериментальной группе."""

    MULTI_AGENT = "multi_agent"
    OPENCLAW = "openclaw"


GROUP_TO_BACKEND = {
    ExperimentGroup.GROUP_A: AgentBackend.MULTI_AGENT,
    ExperimentGroup.GROUP_B: AgentBackend.OPENCLAW,
}


def assign_group() -> ExperimentGroup:
    """Случайное назначение группы 50/50."""
    return random.choice([ExperimentGroup.GROUP_A, ExperimentGroup.GROUP_B])


def parse_experiment_group(value: str | ExperimentGroup) -> ExperimentGroup:
    """Строка → ExperimentGroup, только для финальных буквенных групп."""
    return value if isinstance(value, ExperimentGroup) else ExperimentGroup(value)


def backend_for_group(group: str | ExperimentGroup) -> AgentBackend:
    """Определить бэкенд по группе эксперимента."""
    return GROUP_TO_BACKEND[parse_experiment_group(group)]
