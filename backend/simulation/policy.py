"""Генеративная политика студента.

Ключ анти-тавтологии: студент имеет ЛАТЕНТНЫЙ mode (истинный режим), который
эволюционирует стохастически по чертам (skill/persistence/strategy). Действия
эмитятся УСЛОВНО по mode. То есть mode — ПРИЧИНА, действия — следствие. Детектор
наблюдает действия и пытается вывести mode; поскольку mode порождён независимо
(не из порогов признаков детектора), сравнение детектор(действия) vs mode честно.
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
    progress: float = 0.0          # прогресс по текущему шагу [0,1]
    mode: TrueRegime = TrueRegime.PRODUCTIVE
    frustration: float = 0.0
    just_helped: bool = False
    done: bool = False


def _pick_struggle(profile: StudentProfile, rng: random.Random) -> TrueRegime:
    """Тип затруднения по чертам: низкая strategy → перебор/повтор; иначе застревание."""
    if profile.strategy < 0.4:
        return rng.choice((TrueRegime.TRIAL_AND_ERROR, TrueRegime.REPEATING_ERRORS))
    return rng.choice((TrueRegime.STUCK_ON_STEP, TrueRegime.IDLE))


def _transition_mode(profile: StudentProfile, state: StudentState, rng: random.Random) -> None:
    """Стохастический переход латентного mode по чертам (semi-Markov-ish)."""
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
    """Один шаг: перейти mode, эмитить действие по mode, обновить состояние."""
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
        # в затруднении — шанс попросить помощь (склонность + фрустрация)
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
