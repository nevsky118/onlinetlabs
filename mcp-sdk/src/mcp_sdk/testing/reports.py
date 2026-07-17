"""Decorators and steps for test reporting."""

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import contextmanager


def name(display_name: str) -> Callable:
    """Decorator that sets the test's display name (attaches `display_name` to the function)."""

    def decorator(func: Callable) -> Callable:
        func.display_name = display_name
        return func

    return decorator


@contextmanager
def step(step_name: str) -> Generator[None, None, None]:
    """Context manager for a logical test step; prints "[STEP] <name>" on enter."""
    print(f"[STEP] {step_name}")
    yield


def num(*nums: int | str) -> Callable:
    """Decorator that links the test to its number or ID (attaches `test_nums`)."""

    def decorator(func: Callable) -> Callable:
        func.test_nums = nums
        return func

    return decorator


def external_id(id_: str) -> Callable:
    """Decorator that sets the test's external identifier, e.g. a UUID or TMS key (attaches `external_id`)."""

    def decorator(func: Callable) -> Callable:
        func.external_id = id_
        return func

    return decorator
