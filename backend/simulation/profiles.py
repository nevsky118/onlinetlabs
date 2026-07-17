"""Sim-student's latent profile: traits from distributions, seeded → reproducible."""
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class StudentProfile:
    """Traits in [0,1]. Determine the probabilistic action policy (see policy.py)."""

    skill: float          # 0=novice, 1=expert
    persistence: float    # 0=gives up fast, 1=persistent
    strategy: float       # 0=random trial-and-error, 1=systematic
    pace: float           # 0=slow, 1=fast
    help_propensity: float  # tendency to ask for help


def sample_profile(seed: int) -> StudentProfile:
    """Deterministic profile from a seed."""
    rng = random.Random(seed)
    return StudentProfile(
        skill=rng.betavariate(2.0, 2.0),
        persistence=rng.betavariate(2.0, 2.0),
        strategy=rng.random(),
        pace=rng.random(),
        help_propensity=rng.betavariate(2.0, 3.0),
    )


def sample_cohort(n: int, base_seed: int = 0) -> list[StudentProfile]:
    """Cohort of n profiles (seed = base_seed + i) — diverse and reproducible."""
    return [sample_profile(base_seed + i) for i in range(n)]
