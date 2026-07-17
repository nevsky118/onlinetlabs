"""Оркестратор когорты: пул из N одновременных сессий + очередь, 50 всего по циклу.

Создаёт is_simulated-юзеров, гоняет каждого через policy→actor, пишет ground-truth.
GNS3-специфика (launch лабы + построение actor) инжектится через `provision` —
чтобы тестировать без реального GNS3 и заменить fake-адаптером (power-анализ, follow-on).
"""
import asyncio
import random
from dataclasses import dataclass, field

from models.user import User
from simulation.policy import StudentState, next_step
from simulation.profiles import sample_cohort

_CMD = {"correct_cmd": "config-correct", "wrong_cmd": "config-wrong", "repeat_error": "config-wrong"}


def _default_command_for(action, state) -> str:
    """v1-заглушка команды; реальные per-lab команды — lab-config (T8.3)."""
    return _CMD.get(action.value, "")


@dataclass
class RunReport:
    completed: int = 0
    peak_concurrency: int = 0
    per_student: list = field(default_factory=list)
    failures: list = field(default_factory=list)


async def run_cohort(
    *, n: int, concurrency: int, base_seed: int, db_factory, provision,
    record_truth=None, command_for=_default_command_for, max_steps: int = 200,
    finalize=None,
) -> RunReport:
    """Прогнать n сим-студентов, ≤concurrency одновременно. provision(profile, seed, user_id)
    -> (session_id, actor). record_truth(session_id, window, regime).
    finalize(session_id, user_id, profile, state) — завершение сессии (LabProgress + end_session)."""
    sem = asyncio.Semaphore(concurrency)
    profiles = sample_cohort(n, base_seed)
    peak = {"cur": 0, "max": 0}
    per_student: list = []
    failures: list = []

    async def _run_one(i: int, profile) -> None:
        async with sem:
            peak["cur"] += 1
            peak["max"] = max(peak["max"], peak["cur"])
            try:
                user_id = f"sim-{base_seed}-{i}"
                async with db_factory() as db:
                    db.add(User(
                        id=user_id, email=f"{user_id}@sim.local",
                        is_simulated=True, is_active=True,
                    ))
                    await db.commit()
                session_id, actor = await provision(profile, base_seed + i, user_id)
                rng = random.Random(base_seed + i)
                state = StudentState(total_steps=5)
                window = 0
                for _ in range(max_steps):
                    action, regime, state = next_step(profile, state, rng)
                    await actor.execute(
                        action, cmd=command_for(action, state),
                        help_context={"step": state.step},
                    )
                    if record_truth is not None:
                        await record_truth(session_id, window, regime.value)
                    window += 1
                    if state.done:
                        break
                if finalize is not None:
                    await finalize(session_id, user_id, profile, state)
                per_student.append(
                    {"user_id": user_id, "session_id": session_id, "windows": window}
                )
            except Exception as exc:
                # Единичный сбой провижна (напр. GNS3 ACL 500) не роняет всю когорту.
                failures.append({"i": i, "error": f"{type(exc).__name__}: {exc}"})
            finally:
                peak["cur"] -= 1

    await asyncio.gather(*(_run_one(i, p) for i, p in enumerate(profiles)))
    return RunReport(
        completed=len(per_student), peak_concurrency=peak["max"],
        per_student=per_student, failures=failures,
    )
