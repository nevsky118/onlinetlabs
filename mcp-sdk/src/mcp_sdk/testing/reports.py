"""Decorators and steps for test reporting."""

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import contextmanager


def name(display_name: str) -> Callable:
    """
    Sets the display name of the test.

    :param display_name: Test name.
    :return: Decorator that attaches the `display_name` attribute to the test function.
    """

    def decorator(func: Callable) -> Callable:
        func.display_name = display_name
        return func

    return decorator


@contextmanager
def step(step_name: str) -> Generator[None, None, None]:
    """
    Context manager for a logical test step.

    :param step_name: Step name.
    :return: Context manager for grouping test steps.
    """
    print(f"[STEP] {step_name}")
    yield


def num(*nums: int | str) -> Callable:
    """
    Links the test to its number or ID.

    :param nums: Test number or identifier.
    :return: Decorator that attaches the `test_nums` attribute to the test function.
    """

    def decorator(func: Callable) -> Callable:
        func.test_nums = nums
        return func

    return decorator


def external_id(id_: str) -> Callable:
    """
    Sets the external identifier of the test.

    :param id_: External test identifier (e.g. UUID or a TMS key).
    :return: Decorator that attaches the `external_id` attribute to the test function.
    """

    def decorator(func: Callable) -> Callable:
        func.external_id = id_
        return func

    return decorator
