"""YAML-driven validation runner. Emits an Event stream via asyncio."""

from collections.abc import AsyncIterator
from pathlib import Path

import yaml

from i18n import DEFAULT_LOCALE, Locale, resolve_localized, t
from validation.checks import registry as _registry
from validation.checks.registry import CheckContext, CheckResult
from validation.stream import Event


async def _eval_check(ctx: CheckContext, check: dict) -> CheckResult:
    """Run a single check. Shared logic for run_validation and evaluate_spec."""
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
    except Exception as exc:
        return CheckResult(ok=False, expected=expect, actual={"error": str(exc)})


def _check_record(kind: str, params: dict, result: CheckResult, locale: Locale) -> dict:
    """Serialise one check for the stream, rendering an unobserved outcome in the student's locale."""
    record = {
        "kind": kind,
        "params": params,
        "ok": result.ok,
        "expected": result.expected,
        "actual": dict(result.actual),
    }
    if not result.observed:
        record["observed"] = False
        record["actual"] = {
            **record["actual"],
            "error": t(result.error_key, locale, **result.error_params) if result.error_key else "",
        }
    return record


_LABS_DIR = Path(__file__).parent / "labs"

_spec_cache: dict[str, tuple[float, dict]] = {}


def load_lab_spec(slug: str) -> dict | None:
    """Load the lab's YAML checks spec, cached by mtime. None if the file doesn't exist."""
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


async def evaluate_spec(
    ctx: CheckContext, spec: dict, locale: Locale = DEFAULT_LOCALE
) -> list[dict]:
    """Run all checks in the spec without an SSE stream. Returns a list of step records."""
    accumulated: list[dict] = []
    for step in spec.get("steps") or []:
        step_id = step.get("id", "")
        step_title = resolve_localized(step.get("title"), locale)
        check_results: list[dict] = []
        step_ok = True
        for check in step.get("checks") or []:
            kind = check.get("kind", "")
            params = {k: v for k, v in check.items() if k not in {"kind", "expect"}}
            expect = check.get("expect") or {}
            result = await _eval_check(ctx, check)
            check_results.append(_check_record(kind, params, result, locale))
            if not result.ok:
                step_ok = False
        accumulated.append(
            {"id": step_id, "title": step_title, "ok": step_ok, "checks": check_results}
        )
    return accumulated


async def run_validation(
    ctx: CheckContext,
    spec: dict,
    locale: Locale = DEFAULT_LOCALE,
) -> AsyncIterator[tuple[Event, list]]:
    """Event generator + accumulated step list for the final UPDATE.

    Yields `(Event, steps_snapshot)`. The caller uses Event for SSE, and the
    final steps_snapshot for writing to the DB.
    """
    steps = spec.get("steps") or []
    yield Event("run.start", {"totalSteps": len(steps)}), []

    accumulated_steps: list[dict] = []

    for step in steps:
        step_id = step.get("id", "")
        step_title = resolve_localized(step.get("title"), locale)
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

            record = _check_record(kind, params, result, locale)
            yield (
                Event(
                    "check.result",
                    {
                        "stepId": step_id,
                        "checkIndex": idx,
                        "ok": record["ok"],
                        "expected": record["expected"],
                        "actual": record["actual"],
                        **({"observed": False} if not result.observed else {}),
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
                    "actual": record["actual"],
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


def spec_slugs() -> set[str]:
    """Slugs of every lab validation spec present on disk."""
    return {p.stem for p in _LABS_DIR.glob("*.yaml")}
