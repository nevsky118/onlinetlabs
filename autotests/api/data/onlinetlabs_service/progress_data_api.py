# Генераторы тестовых данных для progress.

from autotests.settings.utils.data_generator_abstraction import DataAbstractionGenerator
from autotests.settings.utils.utils import Randomizer


class StepAttemptData(DataAbstractionGenerator):
    """
    Генерирует payload для попытки прохождения шага.

    :ivar answer: Ответ пользователя.
    :ivar data: Словарь-payload для POST.
    """

    def __init__(self, answer: str = None):
        self.answer = answer or Randomizer.random_string(20)

        self.data = {
            "answer": self.answer,
        }
