"""Generative student policy.

Anti-tautology key: the student has a LATENT mode (true regime) that evolves
stochastically based on traits (skill/persistence/strategy). Actions are emitted
CONDITIONAL on mode: mode is the CAUSE, actions are the effect. The detector
observes actions and tries to infer mode; since mode is generated independently
(not from the detector's feature thresholds), comparing detector(actions) vs mode is honest.
"""

import random
from dataclasses import dataclass
from enum import Enum

from simulation.profiles import StudentProfile


class Action(str, Enum):
    CORRECT_CMD = "correct_cmd"
    WRONG_CMD = "wrong_cmd"
    IDLE = "idle"
    REPEAT_ERROR = "repeat_error"
    ASK_HELP = "ask_help"
    SUBMIT = "submit"


class TrueRegime(str, Enum):
    PRODUCTIVE = "productive"
    STUCK_ON_STEP = "stuck_on_step"
    REPEATING_ERRORS = "repeating_errors"
    IDLE = "idle"
    TRIAL_AND_ERROR = "trial_and_error"


@dataclass
class StudentState:
    total_steps: int = 5
    step: int = 0
    progress: float = 0.0  # progress on the current step [0,1]
    mode: TrueRegime = TrueRegime.PRODUCTIVE
    frustration: float = 0.0
    just_helped: bool = False
    done: bool = False


def _pick_struggle(profile: StudentProfile, rng: random.Random) -> TrueRegime:
    """Struggle type from traits: low strategy → trial-and-error/repeat; else stuck."""
    if profile.strategy < 0.4:
        return rng.choice((TrueRegime.TRIAL_AND_ERROR, TrueRegime.REPEATING_ERRORS))
    return rng.choice((TrueRegime.STUCK_ON_STEP, TrueRegime.IDLE))


def _transition_mode(profile: StudentProfile, state: StudentState, rng: random.Random) -> None:
    """Stochastic transition of the latent mode based on traits (semi-Markov-ish)."""
    if state.mode == TrueRegime.PRODUCTIVE:
        if rng.random() < (1.0 - profile.skill) * 0.25:
            state.mode = _pick_struggle(profile, rng)
    else:
        recover = profile.persistence * 0.15 + (0.35 if state.just_helped else 0.0)
        if rng.random() < recover:
            state.mode = TrueRegime.PRODUCTIVE
            state.frustration = max(0.0, state.frustration - 0.3)
        elif state.frustration > 0.6 and rng.random() < (1.0 - profile.persistence) * 0.4:
            state.mode = TrueRegime.IDLE
    state.just_helped = False


def next_step(
    profile: StudentProfile, state: StudentState, rng: random.Random
) -> tuple[Action, TrueRegime, StudentState]:
    """One step: transition mode, emit an action based on mode, update state."""
    if state.step >= state.total_steps:
        state.done = True
        return Action.SUBMIT, TrueRegime.PRODUCTIVE, state

    _transition_mode(profile, state, rng)
    mode = state.mode

    if mode == TrueRegime.PRODUCTIVE:
        action = Action.CORRECT_CMD
        state.progress += 0.34
        state.frustration = max(0.0, state.frustration - 0.1)
        if state.progress >= 1.0:
            state.step += 1
            state.progress = 0.0
            if state.step >= state.total_steps:
                state.done = True
                return Action.SUBMIT, mode, state
    else:
        # while struggling, chance to ask for help (propensity + frustration)
        if rng.random() < profile.help_propensity * 0.4 + state.frustration * 0.2:
            action = Action.ASK_HELP
            state.just_helped = True
            state.frustration = max(0.0, state.frustration - 0.15)
        elif mode == TrueRegime.REPEATING_ERRORS:
            action = Action.REPEAT_ERROR
            state.frustration = min(1.0, state.frustration + 0.15)
        elif mode == TrueRegime.TRIAL_AND_ERROR:
            action = Action.WRONG_CMD
            state.frustration = min(1.0, state.frustration + 0.1)
        elif mode == TrueRegime.IDLE:
            action = Action.IDLE
            state.frustration = min(1.0, state.frustration + 0.1)
        else:  # STUCK_ON_STEP
            action = Action.WRONG_CMD if rng.random() < 0.5 else Action.IDLE
            state.frustration = min(1.0, state.frustration + 0.12)

    return action, mode, state
