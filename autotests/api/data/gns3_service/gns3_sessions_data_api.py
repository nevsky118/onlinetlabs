# Генераторы данных для GNS3 sessions.

from autotests.settings.utils.data_generator_abstraction import DataAbstractionGenerator
from autotests.settings.utils.utils import Randomizer


class Gns3SessionCreateData(DataAbstractionGenerator):
    """
    Генерирует payload для POST /sessions.

    :ivar user_id: ID пользователя платформы.
    :ivar lab_template_project_id: UUID шаблонного проекта GNS3.
    :ivar data: Словарь-payload для POST.
    """

    def __init__(self, user_id: str = None, lab_template_project_id: str = None):
        self.user_id = user_id or f"user-{Randomizer.random_string(6).lower()}"
        self.lab_template_project_id = lab_template_project_id or Randomizer.uuid()

        self.data = {
            "user_id": self.user_id,
            "lab_template_project_id": self.lab_template_project_id,
        }
