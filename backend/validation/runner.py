"""YAML-driven validation runner. Emits Event-stream через asyncio."""

from pathlib import Path
from typing import AsyncIterator

import yaml

from validation.checks import registry as _registry
from validation.checks.registry import CheckContext, CheckResult
from validation.stream import Event


async def _eval_check(ctx: CheckContext, check: dict) -> CheckResult:
    """Выполнить одну проверку — общая логика для run_validation и evaluate_spec."""
    kind = check.get("kind", "")
    params = {k: v for k, v in check.items() if k not in {"kind", "expect"}}
    expect = check.get("expect") or {}
    handler = _registry.get_handler(kind)
    if handler is None:
        return CheckResult(
            ok=False, expected=expect, actual={"error": f"unknown check kind: {kind}"}
        )
    try:
        return await handler(ctx, params, expect)
    except Exception as exc:  # noqa: BLE001
        return CheckResult(ok=False, expected=expect, actual={"error": str(exc)})


_LABS_DIR = Path(__file__).parent / "labs"

_spec_cache: dict[str, tuple[float, dict]] = {}


def load_lab_spec(slug: str) -> dict | None:
    """Загрузить YAML-спеку проверок лабы с кешем по mtime. None, если файла нет."""
    path = _LABS_DIR / f"{slug}.yaml"
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    cached = _spec_cache.get(slug)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    with path.open("r", encoding="utf-8") as fh:
        spec = yaml.safe_load(fh)
    _spec_cache[slug] = (mtime, spec)
    return spec


async def evaluate_spec(ctx: CheckContext, spec: dict) -> list[dict]:
    """Прогнать все проверки spec без SSE-стрима. Возвращает список step-records."""
    accumulated: list[dict] = []
    for step in spec.get("steps") or []:
        step_id = step.get("id", "")
        step_title = step.get("title", "")
        check_results: list[dict] = []
        step_ok = True
        for check in step.get("checks") or []:
            kind = check.get("kind", "")
            params = {k: v for k, v in check.items() if k not in {"kind", "expect"}}
            expect = check.get("expect") or {}
            result = await _eval_check(ctx, check)
            check_results.append(
                {
                    "kind": kind,
                    "params": params,
                    "ok": result.ok,
                    "expected": result.expected,
                    "actual": result.actual,
                }
            )
            if not result.ok:
                step_ok = False
        accumulated.append(
            {"id": step_id, "title": step_title, "ok": step_ok, "checks": check_results}
        )
    return accumulated


async def run_validation(
    ctx: CheckContext,
    spec: dict,
) -> AsyncIterator[tuple[Event, list]]:
    """Generator событий + накопленный список шагов для финального UPDATE.

    Yield-ит `(Event, steps_snapshot)`. Caller использует Event для SSE,
    а финальный steps_snapshot — для записи в БД.
    """
    steps = spec.get("steps") or []
    yield Event("run.start", {"totalSteps": len(steps)}), []

    accumulated_steps: list[dict] = []

    for step in steps:
        step_id = step.get("id", "")
        step_title = step.get("title", "")
        checks = step.get("checks") or []
        yield (
            Event(
                "step.start",
                {"stepId": step_id, "title": step_title, "totalChecks": len(checks)},
            ),
            accumulated_steps,
        )

        check_results: list[dict] = []
        step_ok = True

        for idx, check in enumerate(checks):
            kind = check.get("kind", "")
            params = {k: v for k, v in check.items() if k not in {"kind", "expect"}}
            yield (
                Event(
                    "check.start",
                    {
                        "stepId": step_id,
                        "checkIndex": idx,
                        "kind": kind,
                        "params": params,
                    },
                ),
                accumulated_steps,
            )

            result = await _eval_check(ctx, check)

            for line in (result.log or "").splitlines():
                yield (
                    Event(
                        "check.log",
                        {
                            "stepId": step_id,
                            "checkIndex": idx,
                            "line": line,
                        },
                    ),
                    accumulated_steps,
                )

            yield (
                Event(
                    "check.result",
                    {
                        "stepId": step_id,
                        "checkIndex": idx,
                        "ok": result.ok,
                        "expected": result.expected,
                        "actual": result.actual,
                    },
                ),
                accumulated_steps,
            )

            check_results.append(
                {
                    "kind": kind,
                    "params": params,
                    "ok": result.ok,
                    "expected": result.expected,
                    "actual": result.actual,
                }
            )
            if not result.ok:
                step_ok = False

        step_record = {
            "id": step_id,
            "title": step_title,
            "ok": step_ok,
            "checks": check_results,
        }
        accumulated_steps.append(step_record)
        yield (
            Event(
                "step.result",
                {"stepId": step_id, "title": step_title, "ok": step_ok},
            ),
            accumulated_steps,
        )

    overall_ok = all(s["ok"] for s in accumulated_steps) if accumulated_steps else True
    yield Event("run.finish", {"ok": overall_ok}), accumulated_steps
