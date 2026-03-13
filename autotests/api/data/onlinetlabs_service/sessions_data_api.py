# Генераторы тестовых данных для sessions.

from autotests.settings.utils.data_generator_abstraction import DataAbstractionGenerator
from autotests.settings.utils.utils import Randomizer


class SessionCreateData(DataAbstractionGenerator):
    """
    Генерирует payload для создания сессии.

    :ivar lab_slug: Slug лабораторной работы.
    :ivar data: Словарь-payload для POST.
    """

    def __init__(self, lab_slug: str = None):
        uid = Randomizer.uuid()
        self.lab_slug = lab_slug or f"lab-{Randomizer.random_string(8).lower()}"

        self.data = {
            "lab_slug": self.lab_slug,
        }


class SessionUpdateData(DataAbstractionGenerator):
    """
    Генерирует payload для обновления статуса сессии.

    :ivar status: Новый статус сессии.
    :ivar data: Словарь-payload для PATCH.
    """

    def __init__(self, status: str = "completed"):
        self.status = status

        self.data = {
            "status": self.status,
        }
