"""Декораторы и шаги для отчётности тестов."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Callable, Generator


def name(display_name: str) -> Callable:
    """
    Устанавливает отображаемое наименование теста.

    :param display_name: Наименование теста.
    :return: Декоратор, навешивающий на тестовую функцию атрибут `display_name`.
    """

    def decorator(func: Callable) -> Callable:
        func.display_name = display_name
        return func

    return decorator


@contextmanager
def step(step_name: str) -> Generator[None, None, None]:
    """
    Контекстный менеджер логического шага теста.

    :param step_name: Название шага.
    :return: Контекстный менеджер для группировки шагов теста.
    """
    print(f"[STEP] {step_name}")
    yield


def num(*nums: int | str) -> Callable:
    """
    Связывает тест с его номером или ID.

    :param nums: Номер или идентификатор теста.
    :return: Декоратор, навешивающий на тестовую функцию атрибут `test_nums`.
    """

    def decorator(func: Callable) -> Callable:
        func.test_nums = nums
        return func

    return decorator


def external_id(id_: str) -> Callable:
    """
    Устанавливает внешний идентификатор теста.

    :param id_: Внешний идентификатор теста (например, UUID или ключ из TMS).
    :return: Декоратор, навешивающий на тестовую функцию атрибут `external_id`.
    """

    def decorator(func: Callable) -> Callable:
        func.external_id = id_
        return func

    return decorator
