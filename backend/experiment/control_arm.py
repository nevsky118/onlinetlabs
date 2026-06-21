"""Ось эксперимента loop on/off: open (без проактива) vs closed (замкнутый контур)."""
import random
from enum import Enum


class ControlArm(str, Enum):
    OPEN = "open"      # заземлённый реактивный чат, проактив подавлен
    CLOSED = "closed"  # замкнутый контур


def assign_arm() -> ControlArm:
    """Случайное назначение плеча 50/50."""
    return random.choice([ControlArm.OPEN, ControlArm.CLOSED])
