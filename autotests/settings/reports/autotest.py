from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Callable, Generator


def name(display_name: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.display_name = display_name
        return func
    return decorator


@contextmanager
def step(step_name: str) -> Generator[None, None, None]:
    print(f"[STEP] {step_name}")
    yield


def num(*nums: int | str) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.test_nums = nums
        return func
    return decorator


def external_id(id_: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.external_id = id_
        return func
    return decorator
