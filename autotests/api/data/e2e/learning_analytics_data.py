# Генераторы тестовых данных для e2e тестов Learning Analytics.


class MCPContextTestData:
    """
    Тестовые данные для e2e проверки MCP → AgentContext → LLM пайплайна.

    :ivar project_name: Имя GNS3 проекта.
    :ivar user_question: Вопрос студента для TutorAgent.
    :ivar struggle_type: Тип проблемы для AgentContext.
    :ivar dominant_error: Доминирующая ошибка.
    """

    def __init__(self):
        self.project_name = "e2e-la-test"
        self.user_question = "Почему PC1 и PC2 не могут обмениваться данными?"
        self.struggle_type = "repeating_errors"
        self.dominant_error = "VLAN 10 not found"


class HintTestData:
    """
    Тестовые данные для проверки HintAgent.

    :ivar step_slug: Шаг, на котором застрял студент.
    :ivar last_error: Последняя ошибка.
    :ivar attempts_count: Кол-во попыток (определяет hint_level).
    """

    def __init__(self, attempts_count: int = 4):
        self.step_slug = "step-1"
        self.last_error = "VLAN 10 not found on SW1"
        self.attempts_count = attempts_count
