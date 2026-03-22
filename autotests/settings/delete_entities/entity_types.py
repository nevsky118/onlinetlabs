# Перечисление типов сущностей для автоочистки.

from enum import Enum


class EntitiesTypes(Enum):
    """
    Типы сущностей, создаваемых в тестах.

    Порядок важен: верхние удаляются первыми.
    """

    gns3_project = "gns3_project"
    gns3_session = "gns3_session"
    session = "session"
    user = "user"
