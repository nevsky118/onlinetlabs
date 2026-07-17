"""Латентный профиль сим-студента: черты из распределений, seeded → воспроизводимо."""
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class StudentProfile:
    """Черты в [0,1]. Определяют вероятностную политику действий (см. policy.py)."""

    skill: float          # 0=новичок, 1=эксперт
    persistence: float    # 0=быстро сдаётся, 1=упорный
    strategy: float       # 0=перебор наугад, 1=систематик
    pace: float           # 0=медленный, 1=быстрый
    help_propensity: float  # склонность просить помощь


def sample_profile(seed: int) -> StudentProfile:
    """Детерминированный профиль по seed."""
    rng = random.Random(seed)
    return StudentProfile(
        skill=rng.betavariate(2.0, 2.0),
        persistence=rng.betavariate(2.0, 2.0),
        strategy=rng.random(),
        pace=rng.random(),
        help_propensity=rng.betavariate(2.0, 3.0),
    )


def sample_cohort(n: int, base_seed: int = 0) -> list[StudentProfile]:
    """Когорта из n профилей (seed = base_seed + i) — разнообразно и воспроизводимо."""
    return [sample_profile(base_seed + i) for i in range(n)]
